# RouteWise AI

A responsive logistics dashboard for managing delivery orders, tracking status, reviewing deadline/priority alerts, exporting deadline-filtered reports, and requesting road-network route estimates. The UI is plain HTML/CSS/JavaScript; the API is FastAPI backed by SQLite.

> **Prototype / hackathon deployment only:** there is currently no sign-in or authorization layer. CORS limits browser origins but does not secure the API from direct requests. Do not put live customer information on a public deployment until you add authentication, authorization, and appropriate privacy controls.

## What is implemented

- Delivery CRUD with case-insensitive unique order IDs, server-side validation, status history, filters and CSV export.
- Operations dashboard with counts, overdue and high-priority indicators, plus transparent rule-based dispatch prompts. This is not machine learning; dispatch prompts rank overdue/high-priority work, while route order is optimized separately.
- Leaflet maps with OpenStreetMap tiles; Nominatim address lookup; OSRM driving-profile route ordering and estimates, labelled as estimates without live traffic.
- Delivery proof upload through a backend-signed Cloudinary flow; upload metadata and status changes are recorded in delivery history.
- Empty-on-first-run SQLite database, `/api/health`, and interactive OpenAPI/Swagger documentation at `/docs`.
- GitHub Pages frontend workflow and a Render Blueprint for the FastAPI backend.

External routing/geocoding/Cloudinary behavior depends on those providers being reachable and correctly configured. No live Cloudinary upload or hosted deployment has been completed or claimed in this repository.

## Repository layout

```text
frontend/                 Static app (index.html, styles.css, app.js, config.js)
backend/app/              FastAPI app, Pydantic schemas, SQLite and external services
backend/requirements.txt  Backend runtime dependencies
requirements.txt          Runtime plus pytest dependencies
tests/                     API integration tests (isolated temporary SQLite database)
docs/                     API, deployment, architecture, demo and planning material
.github/workflows/        GitHub Pages deployment workflow
render.yaml               Render service blueprint
.env.example              Placeholder configuration only
```

## Run locally

Requirements: Python 3.10+.

```bash
cd routewise-ai
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

The app reads environment variables from the process; it does not automatically load `.env`. Set them in your shell or your hosting provider. For a quick local run, the defaults are suitable except the Nominatim User-Agent should be changed before geocoding:

```bash
export DATABASE_PATH=./routewise.db
export CORS_ORIGINS=http://localhost:8000
export NOMINATIM_USER_AGENT='RouteWiseAI/1.0 (replace-with-your-contact-email)'
uvicorn app.main:app --app-dir backend --reload
```

Open `http://127.0.0.1:8000` only if you serve the frontend from the same origin; otherwise serve `frontend/` with a static web server and set `frontend/config.js` to the API origin. For example, from the project root, `python -m http.server 8001 --directory frontend` then set `apiBaseUrl` to `http://127.0.0.1:8000` and set `CORS_ORIGINS=http://localhost:8001`. The API docs are at `http://127.0.0.1:8000/docs`.

The database is created automatically and starts empty. Do not commit `.env`, SQLite database files, or real customer records.

## Configuration

See [`.env.example`](.env.example) for the full list. Key settings:

- `DATABASE_PATH`: SQLite file path; use durable storage for hosted data.
- `CORS_ORIGINS`: comma-separated exact frontend origins, with scheme and host (no wildcard).
- `NOMINATIM_USER_AGENT`: identify your app and provide a real contact route before using the public Nominatim service. Requests are throttled (default minimum interval: 1.1 seconds).
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_UPLOAD_PRESET`: set only on the backend. API secret is never sent to the browser.
- `MAX_UPLOAD_BYTES`: application-side client size check (default 10 MiB). Also enforce file type/size restrictions in the Cloudinary upload preset; browser checks alone can be bypassed.

The browser configuration file contains only the public API base URL. Never place the Cloudinary API secret in it.

## Tests and checks

```bash
python -m pytest -q
node --check frontend/app.js
```

The API test suite uses a temporary SQLite database and stubs external route calls where appropriate. These tests do not verify live Nominatim, OSRM, OpenStreetMap tile, Cloudinary account, or production-host behavior. For current verification results and limitations, see [`docs/verification.md`](docs/verification.md).

## Deploy

Follow [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). In brief: deploy `frontend/` through the included GitHub Pages workflow, deploy the FastAPI service from `render.yaml` with a persistent disk, set the exact CORS and provider values, then update `frontend/config.js` with the deployed backend origin and verify health, CORS, CRUD, and external integrations. Hosting a durable SQLite disk may require a paid service plan; check current provider pricing and terms before creating resources.

## Security and known limitations

- **No user authentication/authorization is implemented.** Anyone able to reach the API can read, change, or delete its records. CORS is not an access-control mechanism. Add a proper identity/session and role model before storing real delivery/customer data on a publicly reachable backend.
- Configure CORS to the exact Pages origin. Never use `*` for a public deployment.
- Store Cloudinary secrets only in the backend environment. Constrain the upload preset to images and the intended file-size ceiling as well as using the UI checks. Check account quotas and provider retention settings.
- Nominatim and the public OSRM endpoint are shared public services, may rate-limit or be unavailable, and are not a production SLA. Use an appropriate service/provider for sustained production workloads and honor provider policies.
- Route distance and duration are OSRM estimates, not actual travel records or live-traffic predictions. Prioritization and route optimization are separate: urgent/overdue prompts use status, priority, and deadlines; route order is returned by OSRM for the stops the operator selects.
- SQLite is appropriate for this demonstrator and a single service with a durable local disk; it is not a substitute for a multi-writer production database.

See [API reference](docs/API.md), [architecture](docs/architecture.md), [demo walkthrough](docs/demo-walkthrough.md), [presentation outline](docs/presentation-outline.md), and [Notion project template](docs/notion-template.md).
