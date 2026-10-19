# RouteWise AI — Hacktober HackDays 2026

**Tagline:** Smarter Routes. Faster Deliveries. Less Waste.

## Team
- Member 1 — UI, delivery management, route heuristic, map integration
- Member 2 — Cloudinary integration, testing, documentation, demo

## Problem statement
Small delivery teams may lack an affordable, clear workflow for managing shipment status, prioritising urgent stops, and planning a reasonable delivery sequence. Manual processes can make it harder to see overdue work and coordinate multiple destinations.

## Proposed solution
RouteWise AI is a mobile-friendly delivery management prototype. It maintains delivery records, shows stops on a map, suggests a stop order using a nearest-neighbour heuristic, identifies overdue/due-soon/high-priority shipments with explainable rules, and stores parcel/proof images in Cloudinary.

## MVP scope
- [ ] Add/edit/delete/search/filter deliveries
- [ ] Delivery status and priority tracking
- [ ] Map markers using Leaflet/OpenStreetMap
- [ ] Nearest-neighbour route ordering and Haversine estimate
- [ ] Cloudinary unsigned image upload tested against our account
- [ ] Explainable dispatch insights
- [ ] LocalStorage persistence and CSV export
- [ ] Responsive mobile layout
- [ ] GitHub Pages live deployment

## Architecture
- Frontend: HTML, CSS, vanilla JavaScript
- Map: Leaflet + OpenStreetMap tiles
- Geocoding: OpenStreetMap Nominatim lookup (manual verification required)
- Image storage: Cloudinary unsigned upload preset
- Local demo persistence: browser LocalStorage
- Hosting: GitHub Pages

## Data model
`id`, `recipient`, `packageName`, `address`, `lat`, `lng`, `priority`, `dueDate`, `status`, `imageUrl`, `imagePublicId`, `createdAt`.

## Daily build log
### 19 Oct 2026 — Planning and initial implementation
- Completed:
- Commit/link:
- Decisions:
- Blockers:
- Next steps:

### 20 Oct 2026
- Completed:
- Commit/link:
- Decisions:
- Blockers:
- Next steps:

### 21 Oct 2026
- Completed:
- Commit/link:
- Cloudinary upload test result (no secrets):
- Blockers:
- Next steps:

### 22 Oct 2026
- Completed:
- Commit/link:
- Route/insight tests:
- Blockers:
- Next steps:

### 23 Oct 2026
- Completed:
- Live demo URL:
- Mobile QA results:
- Bugs fixed:

### 24 Oct 2026
- Final README/demo/video links:
- Submission review:
- Remaining limitations:

## Test evidence
| Test | Expected | Actual result | Pass/fail | Screenshot/notes |
|---|---|---|---|---|
| Create delivery | Record appears in list and map | | | |
| Refresh browser | Record remains in same browser | | | |
| Update status | Status and counters update | | | |
| Due date yesterday | Overdue insight appears | | | |
| High priority | Priority flag appears | | | |
| Invalid coordinate | Form validation blocks save | | | |
| Cloudinary valid image | Upload returns secure URL | | | |
| Cloudinary upload failure | Clear error is shown | | | |
| CSV export | Download contains records | | | |
| Mobile layout | Controls remain usable | | | |

## Cloudinary integration evidence
- Cloud name configured: (do not paste API secrets)
- Unsigned preset configured: (preset name only)
- Upload test image: 
- Resulting secure URL (optional):
- Upload restrictions enabled:

## Known limitations
- LocalStorage is browser/device-local and not shared across users.
- No authentication or production backend.
- Route ordering is a heuristic, not a global optimum.
- Distance is straight-line, not road distance.
- No live GPS tracking or traffic-aware ETA.
- Geocoding and map assets require internet.

## Demo script (90 seconds)
1. Explain the delivery coordination problem.
2. Add a delivery with coordinates and priority.
3. Show map markers and route optimisation.
4. Show overdue/due-soon/high-priority insights.
5. Upload an image through Cloudinary.
6. Export delivery CSV.
7. Summarise limitations and future roadmap.

## Final submission links
- GitHub repository:
- GitHub Pages demo:
- Notion documentation (public view access):
- Demo video:
- Unstop submission confirmation:
