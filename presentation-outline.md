# Hackathon presentation outline (7 slides, ~5 minutes)

## 1. RouteWise AI — Last-mile delivery operations
- One view for orders, dispatch attention, and estimated stop ordering.
- Team / event / date: [fill in]. Do not add an unverified deployment link.

## 2. The operational problem
- Disconnected order lists obscure delivery deadlines and urgent work.
- Dispatchers need to coordinate status and route context quickly.
- Use a sourced user interview/operational example if available; do not invent adoption or savings figures.

## 3. Product walkthrough
- Dashboard and live, user-entered delivery records.
- Search/filter, status history, proof event, and CSV reporting.
- Clearly identify demo data as temporary and manually entered.

## 4. Routing and insights
- OSRM driving-profile stop ordering with estimated distance/time and road geometry.
- Separate rule-based deadline/priority briefing; no ML model or live traffic claim.
- Show an observed result only; otherwise show graceful failure state.

## 5. Architecture and reliability
- Vanilla static frontend; FastAPI + Pydantic; SQLite; Leaflet/OpenStreetMap.
- Nominatim requests are identified/throttled; OSRM route results are estimates.
- Cloudinary signed-upload design keeps API secret backend-only; live account upload verification is still a manual step unless completed and evidenced.

## 6. Validation and honest status
- Report the exact pytest result, commit/environment, and what tests cover.
- Separate unit/API tests from external-provider and visual/browser checks.
- State no deployment, live Cloudinary upload, route result, or customer impact unless actually verified.

## 7. Next steps / ask
- Add authentication and authorization before storing real customer data.
- Complete provider setup, deployment smoke tests, and security/privacy review.
- Later: production routing provider, durable database strategy, observability, and real operational evaluation.
- Ask: [specific mentor, pilot, or resource needed].
