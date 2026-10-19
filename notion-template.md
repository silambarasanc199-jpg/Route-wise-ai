# RouteWise AI — Notion workspace template

Duplicate these sections into a project workspace. Keep customer addresses and credentials out of the public demo workspace.

## Project overview
- **Project:** RouteWise AI — Smart Logistics & Delivery Optimization
- **Problem / target user:** [Describe the last-mile coordination problem and who experiences it]
- **Value proposition:** [What decisions become easier or faster?]
- **Status:** Prototype; manual deployment and provider setup required
- **Owner / team:** [Names and roles]
- **Repository / live links:** [Add only after actually created and verified]

## Goals and non-goals
- Goals: manage delivery records, expose status/deadline risks, estimate stop order on a road network, retain status/proof history.
- Non-goals (current): live fleet telemetry, live traffic, ML demand prediction, authenticated multi-user production service.
- Success measures: [Baseline], [target], [measurement period], [data owner]. Never enter fabricated operational metrics.

## Build and run
- Local setup: see repository `README.md`.
- Backend API/deployment: see `docs/API.md` and `docs/DEPLOYMENT.md`.
- Decisions: [Date] — [Decision] — [Reason] — [Owner].
- Risks / issues: [Risk], [severity], [mitigation], [owner], [review date].

## Feature board
Create a database with fields: **Task**, **Area** (Frontend / API / Data / Maps / Uploads / Deploy / Security), **Status**, **Priority**, **Owner**, **Due date**, **Acceptance checks**, **Evidence / link**, **Blocker**.

Suggested acceptance checks:
- [ ] API health succeeds against the target backend.
- [ ] A new record persists after a restart and invalid/duplicate input is rejected.
- [ ] Status transitions appear in event history.
- [ ] Route estimate displays an explicit estimate disclaimer; failures display no invented metrics.
- [ ] Proof upload succeeds in the configured Cloudinary account and is visible in record history (attach evidence only if tested).
- [ ] Published site works at desktop and phone widths; exact CORS origin is configured.
- [ ] Authentication/authorization and privacy review are completed before storing real customer data.

## Test and release log
Use one row per actual run: **Timestamp + timezone**, **commit**, **command/URL**, **environment**, **result**, **scope covered**, **limitations**, **operator**. Separate automated tests from manual provider verification. Never copy placeholder URLs or claim a test that was not performed.

## Demo checklist
- [ ] Start with the empty database and state the service boundaries.
- [ ] Enter clearly marked disposable demo records during the session; do not commit seeded records.
- [ ] Show filters, status history, and the rules-based briefing.
- [ ] Show OSRM route estimate/disclaimer or explain an observed provider outage.
- [ ] Show proof upload only if credentials and a real upload are verified.
- [ ] End with remaining security/deployment work and next steps.
