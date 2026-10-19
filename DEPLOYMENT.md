# Deployment and provider setup

This project does not deploy itself. You need a GitHub repository, provider accounts, and manual configuration. Do not commit credentials. Check live provider pricing/terms before provisioning; a persistent Render disk generally requires a paid service plan.

## 1. Create and push a GitHub repository

1. Create a new, private or public repository and push the contents of this project to its root (so `render.yaml` and `.github/workflows/pages.yml` are at repository root).
2. Confirm `.env`, database files, and customer data are not committed. `.gitignore` excludes them.
3. GitHub repository → **Settings → Pages** → set the source to **GitHub Actions**. The included workflow deploys only `frontend/` on pushes to `main` and supports manual runs.
4. Ensure the workflow has the permissions shown in `pages.yml`; approve the environment/deployment if GitHub prompts.
5. Wait for the Actions workflow to succeed. Copy the Pages URL. The origin is the scheme+host only, e.g. `https://account.github.io`.

## 2. Deploy the API on Render (or an equivalent Python host)

`render.yaml` defines a Python web service rooted at `backend/`, health-check path `/api/health`, SQLite path `/var/data/routewise.db`, and a durable disk. Review the Blueprint in Render before applying. Select a plan compatible with persistent disks and check current charges. If using another platform, configure equivalent persistent storage and environment values yourself.

Set the backend environment:

- `DATABASE_PATH=/var/data/routewise.db` (or the provider's persistent mount path).
- `CORS_ORIGINS=https://<account>.github.io` (include only exact, trusted origins; comma-separate multiple).
- `NOMINATIM_USER_AGENT=RouteWiseAI/1.0 (your real contact email or URL)`.
- Optional Cloudinary values: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_UPLOAD_PRESET`, and optional `CLOUDINARY_FOLDER`, `MAX_UPLOAD_BYTES`.

Keep the Cloudinary API secret in the backend service's secret environment settings only. Configure the Cloudinary preset for permitted image formats and a maximum upload size consistent with `MAX_UPLOAD_BYTES` (default 10 MiB). Cloudinary configuration is optional for other app features; proof upload will report a setup error until configured.

Deploy, then verify `https://<api-host>/api/health` reports database connected and `https://<api-host>/docs` loads. Check provider logs and persistent storage before adding real data.

## 3. Connect GitHub Pages to the API

Edit `frontend/config.js` in the repository to set the public API origin:

```js
window.ROUTEWISE_CONFIG = {
  apiBaseUrl: "https://<your-api-host>"
};
```

Do not include `/api` at the end; the frontend adds `/api` itself. Commit and push. The Pages workflow should redeploy. Confirm CORS permits the published site origin; if you change domain, update `CORS_ORIGINS` too.

## 4. Manual smoke test

Use the published page only after the API health check succeeds:

1. Confirm the dashboard says API connected and displays zero records in a new database.
2. Add a real test record you are authorized to use, including verified coordinates; ensure an existing order ID cannot be reused (case-insensitively).
3. Edit it, change status twice, then inspect the history and confirm timestamps/status transitions. Delete the test record after verification if appropriate.
4. Search/filter the record and export a CSV; confirm filters/date semantics.
5. Select a depot and one or more eligible stops and request a route. Confirm result is labelled an estimate, or a clear service error is shown with no route metrics.
6. With Nominatim configured and available, geocode a real address and check the returned location. Respect the service's usage policy.
7. For Cloudinary, test only after preset restrictions/credentials are configured. Upload a small permitted image, confirm Cloudinary returns success and that proof appears in record history. Confirm a disallowed type/oversize file is rejected. Never claim this step passed unless you actually observe it.
8. Test the narrow/mobile layout and mobile navigation. Check browser console, API logs, and network/CORS errors.

## Important deployment limitations

- The backend has no authentication/authorization. A public API URL permits direct reads/writes/deletes regardless of CORS. Do not store real personal/customer data until proper access controls are implemented.
- Keep secrets out of frontend assets and GitHub history. Rotate any secret accidentally committed.
- SQLite persistence relies on a durable mounted disk and is intended for a small single-service demo, not concurrent multi-instance production.
- Public OSRM/Nominatim services have their own policies and availability; they are not guaranteed production services.
