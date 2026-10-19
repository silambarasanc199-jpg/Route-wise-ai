"""API integration tests run against an isolated SQLite database; no external API calls."""
from dataclasses import replace
import hashlib
import json
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.app import main
from backend.app.database import Database

@pytest.fixture
def client(monkeypatch):
    # SQLite relies on file locking, which is not supported by the remote NFS workspace.
    # Keep test databases on the local ephemeral filesystem instead.
    with tempfile.TemporaryDirectory(prefix="routewise-test-", dir="/tmp") as directory:
        database = Database(str(Path(directory) / "test-routewise.db"))
        monkeypatch.setattr(main, "db", database)
        with TestClient(main.app) as test_client:
            yield test_client


def payload(order_id="RW-1001", **extra):
    data = {"order_id": order_id, "customer_name": "Avery Customer", "address": "17 Example Street, Sampletown", "latitude": 40.7128, "longitude": -74.006, "priority": "normal", "deadline": "2030-05-20T12:00:00Z", "status": "pending"}
    data.update(extra)
    return data


def test_health_check(client):
    response=client.get("/api/health")
    assert response.status_code==200
    assert response.json()=={"status":"ok","database":"connected"}
    assert client.get("/api/deliveries").json()==[]


def test_swagger_and_openapi_schema_are_available(client):
    assert client.get("/docs").status_code==200
    schema=client.get("/openapi.json").json()
    assert schema["info"]["title"]=="RouteWise AI API"
    assert "/api/deliveries" in schema["paths"]


def test_delivery_crud_and_sqlite_persistence(client):
    created=client.post("/api/deliveries",json=payload()).json()
    assert created["order_id"]=="RW-1001"
    assert client.get("/api/deliveries").json()[0]["id"]==created["id"]
    updated=client.patch(f"/api/deliveries/{created['id']}",json={"priority":"high","customer_name":"Avery Updated"})
    assert updated.status_code==200 and updated.json()["priority"]=="high"
    # A fresh Database connection can read the same persisted on-disk SQLite row.
    with Database(main.db.path).connection() as conn:
        assert conn.execute("SELECT customer_name FROM deliveries WHERE id=?", (created["id"],)).fetchone()[0] == "Avery Updated"
    assert client.delete(f"/api/deliveries/{created['id']}").status_code==204
    assert client.get(f"/api/deliveries/{created['id']}").status_code==404


def test_duplicate_order_ids_are_case_insensitive_conflict(client):
    assert client.post("/api/deliveries",json=payload("RW-Repeat")).status_code==201
    response=client.post("/api/deliveries",json=payload("rw-repeat"))
    assert response.status_code==409
    assert "already exists" in response.json()["detail"]


def test_patch_rejects_null_for_required_database_fields(client):
    created=client.post("/api/deliveries",json=payload()).json()
    response=client.patch(f"/api/deliveries/{created['id']}",json={"customer_name":None})
    assert response.status_code==422
    assert "Updated fields cannot be null" in response.json()["detail"][0]["msg"]
    assert client.get(f"/api/deliveries/{created['id']}").json()["customer_name"]=="Avery Customer"

@pytest.mark.parametrize("bad", [{"latitude":91},{"longitude":181},{"priority":"critical"},{"order_id":"bad id"},{"customer_name":"  "},{"deadline":"not-a-date"}])
def test_invalid_delivery_input_is_rejected(client,bad):
    response=client.post("/api/deliveries",json=payload(**bad))
    assert response.status_code==422


def test_status_updates_record_change_history(client):
    created=client.post("/api/deliveries",json=payload()).json()
    result=client.patch(f"/api/deliveries/{created['id']}/status",json={"status":"in_transit"})
    assert result.status_code==200 and result.json()["status"]=="in_transit"
    history=client.get(f"/api/deliveries/{created['id']}/history").json()
    assert [(x["old_value"],x["new_value"]) for x in history]==[("pending","in_transit"),(None,"pending")]
    client.patch(f"/api/deliveries/{created['id']}/status",json={"status":"in_transit"})
    assert len(client.get(f"/api/deliveries/{created['id']}/history").json())==2


def test_dashboard_empty_and_calculated_metrics(client):
    assert client.get("/api/dashboard").json()=={"total":0,"pending":0,"in_transit":0,"completed":0,"delayed":0,"overdue":0,"high_priority":0,"completion_percent":0}
    client.post("/api/deliveries",json=payload("OVERDUE",priority="urgent",deadline="2020-01-01T00:00:00Z"))
    client.post("/api/deliveries",json=payload("DONE",status="completed",deadline="2020-01-01T00:00:00Z"))
    summary=client.get("/api/dashboard").json()
    assert (summary["total"],summary["completed"],summary["overdue"],summary["high_priority"],summary["completion_percent"])==(2,1,1,1,50.0)


def test_route_optimizer_uses_osrm_result_and_returns_stop_order(client,monkeypatch):
    first=client.post("/api/deliveries",json=payload("A")).json()
    second=client.post("/api/deliveries",json=payload("B",latitude=41.0,longitude=-73.0)).json()
    async def fake_route(coords):
        assert coords[0]==(40.0,-74.0)
        return {"distance_meters":12345,"duration_seconds":900,"geometry":{"type":"LineString","coordinates":[[-74,40],[-73,41],[-74,40]]},"ordered_input_indexes":[0,2,1],"service":"OSRM public driving profile","estimated":True,"disclaimer":"Estimate only"}
    monkeypatch.setattr(main.services,"optimize_route",fake_route)
    response=client.post("/api/routes/optimize",json={"depot":{"latitude":40,"longitude":-74,"label":"Hub"},"delivery_ids":[first["id"],second["id"]]})
    assert response.status_code==200
    result=response.json()
    assert result["distance_meters"]==12345 and result["duration_seconds"]==900 and result["estimated"] is True
    assert [stop.get("order_id") for stop in result["ordered_stops"] if stop["type"]=="delivery"]==["B","A"]


def test_route_service_failure_is_explicit_not_fabricated(client,monkeypatch):
    item=client.post("/api/deliveries",json=payload()).json()
    async def unavailable(coords): raise RuntimeError("OSRM offline")
    monkeypatch.setattr(main.services,"optimize_route",unavailable)
    response=client.post("/api/routes/optimize",json={"depot":{"latitude":40,"longitude":-74},"delivery_ids":[item["id"]]})
    assert response.status_code==503 and response.json()["detail"]=="OSRM offline"


def test_cloudinary_signature_endpoint_requires_real_configuration(client,monkeypatch):
    monkeypatch.setattr(main,"settings",replace(main.settings,cloudinary_cloud_name="",cloudinary_api_key="",cloudinary_api_secret="",cloudinary_upload_preset=""))
    assert client.get("/api/uploads/signature").status_code==503


def test_cloudinary_signature_is_signed_with_backend_secret(client,monkeypatch):
    configured=replace(main.settings,cloudinary_cloud_name="demo-cloud",cloudinary_api_key="public-api-key",cloudinary_api_secret="test-secret",cloudinary_upload_preset="proof-preset",cloudinary_folder="routewise/test")
    monkeypatch.setattr(main,"settings",configured)
    response=client.get("/api/uploads/signature")
    assert response.status_code==200
    result=response.json()
    signed=f"folder={result['folder']}&timestamp={result['timestamp']}&upload_preset={result['upload_preset']}test-secret"
    assert result["signature"]==hashlib.sha1(signed.encode()).hexdigest()
    assert "test-secret" not in response.text
    assert result["api_key"]=="public-api-key" and result["max_bytes"]==10*1024*1024


def test_proof_url_validation_and_history_recording(client,monkeypatch):
    monkeypatch.setattr(main,"settings",replace(main.settings,cloudinary_cloud_name="demo-cloud"))
    item=client.post("/api/deliveries",json=payload()).json()
    bad=client.post(f"/api/deliveries/{item['id']}/proof",json={"secure_url":"https://evil.example/image.jpg","public_id":"not/ours"})
    assert bad.status_code==422
    good=client.post(f"/api/deliveries/{item['id']}/proof",json={"secure_url":"https://res.cloudinary.com/demo-cloud/image/upload/proof.jpg","public_id":"routewise/proof.jpg"})
    assert good.status_code==201
    proof=client.get(f"/api/deliveries/{item['id']}/proofs").json()
    assert len(proof)==1 and proof[0]["public_id"]=="routewise/proof.jpg"


def test_filters_and_unknown_delivery(client):
    client.post("/api/deliveries",json=payload("RW-1",priority="high"))
    client.post("/api/deliveries",json=payload("RW-2",priority="low",status="completed"))
    assert [x["order_id"] for x in client.get("/api/deliveries?priority=high").json()]==["RW-1"]
    assert [x["order_id"] for x in client.get("/api/deliveries?search=RW-2&status=completed").json()]==["RW-2"]
    assert client.get("/api/deliveries/not-real").status_code==404
