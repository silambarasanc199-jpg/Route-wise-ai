# Verification record

**Checked:** 2026-10-19 (UTC)  
**Scope:** automated tests and a hosted-browser UI preview. No public deployment or provider account was used.

## Automated checks

- `python -m pytest -q` — **23 passed**, with one upstream Starlette/AnyIO deprecation warning. The API tests use an isolated temporary SQLite file under `/tmp`; routing is stubbed where needed and no provider credentials are used. Coverage includes CRUD, persistence, duplicate IDs, validation, status history, dashboard calculations, route result/error handling, Cloudinary signature/configuration and proof metadata validation, filters, health, Swagger/OpenAPI, frontend structure, status metrics, and visible upload failure handling.
- `node --check frontend/app.js` — passed (no syntax diagnostics).
- `python -m compileall -q backend/app tests` — passed.

## Browser UI checks

The frontend files were previewed in the hosted browser at emulated desktop (**1440 × 1000**) and phone (**390 × 844**) sizes. These are browser viewport checks, not physical-device tests.

- The dashboard rendered six operational metric cards in three desktop columns and two phone columns. There was no horizontal page overflow at 390px.
- OpenStreetMap tiles rendered in the Leaflet maps. No delivery records were seeded; the unconfigured API showed its explicit connection/error state.
- On mobile, the navigation opened, selected Route planner, and closed again with `aria-expanded="false"`.
- With no stops selected, route planning showed “Select at least one delivery stop.” and kept route metrics hidden.
- A mocked Cloudinary HTTP 400 response displayed `Proof upload failed: Mock provider rejection`; this checks the failure UX only, not a real upload.
- The add-delivery dialog was previously checked at 390px and fit within the viewport (x=14px, width=362px, right=376px).

## Not verified / manual steps remaining

- TestClient exercises the API and temporary SQLite persistence, but a deployed backend, GitHub Pages action, Render service, production database, exact production CORS setup, and browser-to-hosted-API connectivity were not tested.
- No live Nominatim lookup, OSRM route response, or Cloudinary upload was performed. Cloudinary requires real backend credentials and a restricted preset; successful upload is not claimed.
- No production authentication/authorization exists. Do not put real customer data on a public backend until access control and privacy safeguards are added.
- Finish provider configuration and perform the manual smoke-test checklist in [`DEPLOYMENT.md`](DEPLOYMENT.md) before presenting external-service results as verified.
