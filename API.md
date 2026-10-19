# RouteWise AI API reference

Base URL: the FastAPI service origin. All paths below include `/api`. OpenAPI UI: `/docs`; schema: `/openapi.json`.

JSON request bodies are validated by Pydantic. Validation errors return 422, unknown delivery IDs return 404, duplicate case-insensitive order IDs return 409, and unavailable external services return 503. The API has no authentication; do not expose customer data publicly.

## Health and operations

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Database connectivity check; returns `{"status":"ok","database":"connected"}` or 503. |
| GET | `/api/dashboard` | Counts by status, overdue open records, high/urgent open records, completion percentage. |

## Deliveries

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/deliveries` | List; optional `status`, `priority`, `search`, `from_date`, `to_date` (ISO dates). Dates filter by deadline. |
| POST | `/api/deliveries` | Create a delivery (201). |
| GET | `/api/deliveries/{delivery_id}` | Read one delivery. |
| PATCH | `/api/deliveries/{delivery_id}` | Update one or more fields; explicit null values are rejected. |
| PATCH | `/api/deliveries/{delivery_id}/status` | Change status and append status history. |
| DELETE | `/api/deliveries/{delivery_id}` | Delete the delivery and its cascading history (204). |
| GET | `/api/deliveries/{delivery_id}/history` | Chronological status/proof event records. |
| GET | `/api/deliveries/{delivery_id}/proofs` | Proof metadata records. |
| POST | `/api/deliveries/{delivery_id}/proof` | Record a Cloudinary secure URL and public ID in history after upload. |

Create fields: `order_id` (1–64 chars; letters, digits, dot, underscore, slash, hyphen; unique ignoring case), `customer_name` (1–160 chars), `address` (4–500 chars), numeric `latitude` (-90…90), `longitude` (-180…180), `priority` (`low`, `normal`, `high`, `urgent`), ISO `deadline`, and optional `status` (`pending`, `in_transit`, `completed`, `delayed`; default pending). Naive datetimes are interpreted as UTC.

Proof body: `{"secure_url":"https://res.cloudinary.com/<configured-cloud>/...","public_id":"..."}`. This endpoint records metadata; the image upload itself is a browser-to-Cloudinary request using the signature below.

## Maps and route estimates

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/geocode?q=...` | Nominatim address search; query 4–300 chars. Returns provider coordinates/display name, 404 if no match, 503 if unavailable. |
| POST | `/api/routes/optimize` | OSRM road-network route estimate for selected records and a fixed starting depot. |

Route request example:

```json
{"depot":{"latitude":40.71,"longitude":-74.00,"label":"Main depot"},"delivery_ids":["<delivery-id>"]}
```

Response includes service, estimated distance in meters, estimated duration in seconds, road geometry, ordered stops, and an estimate disclaimer. The backend returns no fabricated metrics when routing fails. Request accepts 1–100 unique delivery IDs.

## Proof upload signature

`GET /api/uploads/signature` returns a short-lived Cloudinary upload signature, public API key, configured cloud/preset/folder, and UI-side file limits. It returns 503 when any required Cloudinary setting is absent. The API secret remains on the server. The browser uploads directly to Cloudinary, then posts the resulting secure URL/public ID to the proof endpoint. Configure provider-side upload preset limits; do not rely only on client-side validation.

## CORS

`CORS_ORIGINS` is a comma-separated list of exact origins. Origins are not paths. For a GitHub Pages project site, the origin is `https://<account>.github.io` (not the repository path). CORS only controls browser access; it does not authenticate API clients.
