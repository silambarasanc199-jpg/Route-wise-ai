# Demo walkthrough (6–8 minutes)

**Preparation:** Start the backend and frontend locally or use actually deployed URLs. Confirm `/api/health`; the first database should be empty. If the API, geocoding, routing, or Cloudinary is not configured/reachable, say so and demonstrate its visible error state instead of inventing output. Use clearly marked disposable demonstration records entered live by the presenter; do not seed them in the application or commit them.

## 0:00–0:45 — Problem and boundary
“Dispatchers need to see what is due, what is urgent, and how selected stops fit on a road network. RouteWise brings order management, deadline/priority prompts, and route estimates into one responsive dashboard. Estimates are not live traffic or fleet tracking; the prioritization is transparent rules, not machine learning.”

## 0:45–1:30 — Empty, real-data workflow
Show the zero-record dashboard and explain that the database has no preloaded records. Add a disposable demo delivery through the form. Enter a presenter-approved example address and verify coordinates returned by Nominatim, or explain that lookup is unavailable and enter coordinates only if independently known. Save and show the new row and updated dashboard.

## 1:30–2:30 — Management and tracking
Add a second disposable record with a different priority/deadline. Search and filter the table. Edit a field, change status, and open history to show the persisted status event and timestamp. Mention duplicate order IDs and invalid coordinates are rejected server-side. Delete temporary data after the demo if desired.

## 2:30–3:30 — Dispatch briefing and reports
Show the “Priority briefing.” Explain that overdue and high/urgent non-completed orders are derived from recorded status, priority, and deadlines. Open Reports, apply status/priority/deadline filters, and export CSV. Do not present this temporary demo data as operational performance.

## 3:30–5:00 — Map and routing
Open the route planner, set a known depot coordinate, and select the demo records. Request routing. Point to the returned stop order, road distance/time estimate, service label, and no-live-traffic disclaimer. If OSRM is unavailable, show the clear unavailable state and explain that no distance/time is fabricated. Do not equate routing with an optimal fleet schedule or promised arrival time.

## 5:00–5:45 — Proof upload (conditional)
Only if Cloudinary credentials and a restricted image preset are configured: choose a small allowed JPEG/PNG/WebP, upload it, then open history and show the stored proof URL. If not verified, say: “The signed upload flow and configuration are implemented, but this environment has not completed a real Cloudinary upload.” Never stage credentials or claim success without observing provider success and the recorded history event.

## 5:45–6:30 — Architecture and next steps
Point to the FastAPI/SQLite backend, static frontend, Nominatim and OSRM adapters, and Cloudinary upload boundary. State the limitations: no authentication/authorization, shared public map/geocoding/routing services, and SQLite's single-service scope. List manual deployment/security work before real customer data. Invite questions.
