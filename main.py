"""RouteWise AI REST API."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone, date
import hashlib
import hmac
import json
import secrets
from urllib.parse import urlparse
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import db
from . import services
from .schemas import DeliveryInput, DeliveryPatch, StatusUpdate, ProofInput, RouteRequest


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def row_dict(row):
    return dict(row) if row is not None else None

def get_delivery(conn, delivery_id: str):
    return conn.execute("SELECT * FROM deliveries WHERE id=?", (delivery_id,)).fetchone()

def ensure_delivery(conn, delivery_id: str):
    row = get_delivery(conn, delivery_id)
    if not row: raise HTTPException(404, "Delivery not found")
    return row

def duplicate(exc):
    return HTTPException(409, "That order ID already exists")

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.initialize()
    yield

app = FastAPI(title="RouteWise AI API", description="Delivery operations, routing estimates, status history and proof-of-delivery APIs.", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=False, allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"], allow_headers=["Content-Type"])

@app.get("/api/health", tags=["health"])
def health():
    try:
        with db.connection() as conn: conn.execute("SELECT 1").fetchone()
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        raise HTTPException(503, "Database unavailable") from exc

@app.get("/api/deliveries", tags=["deliveries"])
def list_deliveries(status: str | None = None, priority: str | None = None, search: str | None = Query(default=None, max_length=160), from_date: date | None = None, to_date: date | None = None):
    clauses, args = [], []
    if status:
        if status not in {"pending", "in_transit", "completed", "delayed"}: raise HTTPException(422, "Invalid status filter")
        clauses.append("status=?"); args.append(status)
    if priority:
        if priority not in {"low", "normal", "high", "urgent"}: raise HTTPException(422, "Invalid priority filter")
        clauses.append("priority=?"); args.append(priority)
    if search:
        clauses.append("(order_id LIKE ? OR customer_name LIKE ? OR address LIKE ?)"); args.extend([f"%{search}%"] * 3)
    if from_date:
        clauses.append("date(deadline)>=?"); args.append(from_date.isoformat())
    if to_date:
        clauses.append("date(deadline)<=?"); args.append(to_date.isoformat())
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with db.connection() as conn:
        rows = conn.execute(f"SELECT * FROM deliveries{where} ORDER BY deadline ASC, created_at DESC", args).fetchall()
    return [row_dict(r) for r in rows]

@app.post("/api/deliveries", status_code=201, tags=["deliveries"])
def create_delivery(payload: DeliveryInput):
    now, delivery_id = utcnow(), str(uuid4())
    values = payload.model_dump(mode="json")
    with db.connection() as conn:
        try:
            conn.execute("INSERT INTO deliveries(id,order_id,customer_name,address,latitude,longitude,priority,deadline,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)", (delivery_id, values["order_id"], values["customer_name"], values["address"], values["latitude"], values["longitude"], values["priority"], values["deadline"], values["status"], now, now))
            conn.execute("INSERT INTO delivery_history(delivery_id,event_type,old_value,new_value,created_at) VALUES(?,?,?,?,?)", (delivery_id, "status", None, values["status"], now))
        except Exception as exc:
            if "UNIQUE constraint failed: deliveries.order_id" in str(exc): raise duplicate(exc)
            raise
        return row_dict(get_delivery(conn, delivery_id))

@app.get("/api/deliveries/{delivery_id}", tags=["deliveries"])
def read_delivery(delivery_id: str):
    with db.connection() as conn: return row_dict(ensure_delivery(conn, delivery_id))

@app.patch("/api/deliveries/{delivery_id}", tags=["deliveries"])
def update_delivery(delivery_id: str, payload: DeliveryPatch):
    updates = payload.model_dump(exclude_unset=True, mode="json")
    if not updates: raise HTTPException(422, "Provide at least one field to update")
    now = utcnow()
    with db.connection() as conn:
        old = ensure_delivery(conn, delivery_id)
        if "status" in updates and updates["status"] != old["status"]:
            conn.execute("INSERT INTO delivery_history(delivery_id,event_type,old_value,new_value,created_at) VALUES(?,?,?,?,?)", (delivery_id, "status", old["status"], updates["status"], now))
        updates["updated_at"] = now
        sql = ",".join(f"{field}=?" for field in updates)
        try: conn.execute(f"UPDATE deliveries SET {sql} WHERE id=?", (*updates.values(), delivery_id))
        except Exception as exc:
            if "UNIQUE constraint failed: deliveries.order_id" in str(exc): raise duplicate(exc)
            raise
        return row_dict(get_delivery(conn, delivery_id))

@app.patch("/api/deliveries/{delivery_id}/status", tags=["deliveries"])
def update_status(delivery_id: str, payload: StatusUpdate):
    now, new_status = utcnow(), payload.status.value
    with db.connection() as conn:
        old = ensure_delivery(conn, delivery_id)
        if old["status"] != new_status:
            conn.execute("UPDATE deliveries SET status=?,updated_at=? WHERE id=?", (new_status, now, delivery_id))
            conn.execute("INSERT INTO delivery_history(delivery_id,event_type,old_value,new_value,created_at) VALUES(?,?,?,?,?)", (delivery_id, "status", old["status"], new_status, now))
        return row_dict(get_delivery(conn, delivery_id))

@app.delete("/api/deliveries/{delivery_id}", status_code=204, tags=["deliveries"])
def delete_delivery(delivery_id: str):
    with db.connection() as conn:
        ensure_delivery(conn, delivery_id)
        conn.execute("DELETE FROM deliveries WHERE id=?", (delivery_id,))

@app.get("/api/deliveries/{delivery_id}/history", tags=["tracking"])
def delivery_history(delivery_id: str):
    with db.connection() as conn:
        ensure_delivery(conn, delivery_id)
        rows = conn.execute("SELECT id,event_type,old_value,new_value,created_at FROM delivery_history WHERE delivery_id=? ORDER BY created_at DESC,id DESC", (delivery_id,)).fetchall()
    return [row_dict(row) for row in rows]

@app.get("/api/deliveries/{delivery_id}/proofs", tags=["tracking"])
def list_proofs(delivery_id: str):
    with db.connection() as conn:
        ensure_delivery(conn, delivery_id)
        rows = conn.execute("SELECT id,new_value,created_at FROM delivery_history WHERE delivery_id=? AND event_type='proof' ORDER BY created_at DESC", (delivery_id,)).fetchall()
    result=[]
    for row in rows:
        try: item=json.loads(row["new_value"])
        except (ValueError, TypeError): continue
        result.append({"id": row["id"], **item, "created_at": row["created_at"]})
    return result

@app.post("/api/deliveries/{delivery_id}/proof", status_code=201, tags=["tracking"])
def record_proof(delivery_id: str, payload: ProofInput):
    parsed = urlparse(payload.secure_url)
    allowed_host = f"res.cloudinary.com"
    if parsed.scheme != "https" or parsed.hostname != allowed_host or not parsed.path.startswith(f"/{settings.cloudinary_cloud_name}/"):
        raise HTTPException(422, "Proof image must be a secure URL from the configured Cloudinary account")
    if not settings.cloudinary_cloud_name:
        raise HTTPException(503, "Cloudinary is not configured")
    now = utcnow(); value = json.dumps({"secure_url": payload.secure_url, "public_id": payload.public_id}, separators=(",", ":"))
    with db.connection() as conn:
        ensure_delivery(conn, delivery_id)
        conn.execute("INSERT INTO delivery_history(delivery_id,event_type,new_value,created_at) VALUES(?,?,?,?)", (delivery_id, "proof", value, now))
        row = conn.execute("SELECT last_insert_rowid() AS id").fetchone()
    return {"id": row["id"], "secure_url": payload.secure_url, "public_id": payload.public_id, "created_at": now}

@app.get("/api/dashboard", tags=["reports"])
def dashboard():
    now = datetime.now(timezone.utc).isoformat()
    with db.connection() as conn:
        rows = conn.execute("SELECT status,priority,deadline FROM deliveries").fetchall()
    counts = {key: 0 for key in ("pending", "in_transit", "completed", "delayed")}
    high_priority=0; overdue=0
    for row in rows:
        counts[row["status"]] += 1
        if row["priority"] in ("high", "urgent") and row["status"] != "completed": high_priority += 1
        if row["status"] != "completed" and row["deadline"] < now: overdue += 1
    total=len(rows)
    return {"total": total, **counts, "overdue": overdue, "high_priority": high_priority, "completion_percent": round(counts["completed"] * 100 / total, 1) if total else 0}

@app.get("/api/geocode", tags=["maps"])
async def geocode(q: str = Query(min_length=4, max_length=300)):
    try: return await services.geocode_address(q)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(503, str(exc)) from exc

@app.post("/api/routes/optimize", tags=["routes"])
async def route_optimize(payload: RouteRequest):
    if len(set(payload.delivery_ids)) != len(payload.delivery_ids): raise HTTPException(422, "Delivery IDs must be unique")
    with db.connection() as conn:
        records=[]
        for delivery_id in payload.delivery_ids:
            record = ensure_delivery(conn, delivery_id)
            records.append(row_dict(record))
    coords=[(payload.depot.latitude, payload.depot.longitude)] + [(r["latitude"],r["longitude"]) for r in records]
    try: result=await services.optimize_route(coords)
    except LookupError as exc: raise HTTPException(422, str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(503, str(exc)) from exc
    ordered=[]
    for input_index in result["ordered_input_indexes"]:
        if input_index == 0: ordered.append({"type":"depot","label":payload.depot.label})
        elif 1 <= input_index <= len(records):
            record=records[input_index-1]
            ordered.append({"type":"delivery","id":record["id"],"order_id":record["order_id"],"customer_name":record["customer_name"]})
    return {**result,"ordered_stops":ordered,"stop_count":len(records),"start_location":payload.depot.model_dump()}

@app.get("/api/uploads/signature", tags=["uploads"])
def upload_signature():
    required=(settings.cloudinary_cloud_name,settings.cloudinary_api_key,settings.cloudinary_api_secret,settings.cloudinary_upload_preset)
    if not all(required): raise HTTPException(503, "Cloudinary is not configured. Set the four CLOUDINARY_* variables in the backend environment.")
    timestamp=int(datetime.now(timezone.utc).timestamp())
    params={"folder":settings.cloudinary_folder,"timestamp":timestamp,"upload_preset":settings.cloudinary_upload_preset}
    to_sign="&".join(f"{k}={params[k]}" for k in sorted(params))+settings.cloudinary_api_secret
    params["signature"]=hashlib.sha1(to_sign.encode()).hexdigest()
    params["api_key"]=settings.cloudinary_api_key
    params["cloud_name"]=settings.cloudinary_cloud_name
    params["max_bytes"]=settings.max_upload_bytes
    params["allowed_formats"]=["jpg","jpeg","png","webp"]
    return params
