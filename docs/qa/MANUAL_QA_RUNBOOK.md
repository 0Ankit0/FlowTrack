# Manual QA Runbook (Web + Mobile Viewport)

This runbook provides repeatable manual QA steps after running seed data.

## 1) Start Services

Backend:

```bash
PYTHONPATH=backend uv run --project backend uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Frontend (Vite):

```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 3000
```

If port 3000 is occupied, Vite will auto-pick 3001.

## 2) Seed QA Data

From repo root:

```bash
scripts/seed_qa_data.sh
```

Reference data details in `docs/qa/SEED_DATA.md`.

## 3) Web QA Matrix

## Admin (`qa_admin`)

1. Login at `/login`.
2. Open tenant switcher and choose `QA Delivery Org`.
3. Validate dashboard shows seeded metrics:
   - Open Tickets >= 1
   - Active Projects >= 1
   - Releases include `v0.1.0-qa`
4. Navigate and verify pages load:
   - `/tickets`
   - `/projects`
   - `/releases`
5. Open admin surfaces:
   - `/admin/dashboard`
   - `/admin/users`
   - `/admin/rbac`
6. Tenant persistence regression check:
   - Select `QA Delivery Org`.
   - Hard refresh on `/dashboard`, then open `/tickets` and `/projects`.
   - Expected: tenant remains `QA Delivery Org` and tenant-scoped pages do not fall back to Personal.

## PM (`qa_pm`)

1. Login at `/login`.
2. Validate no admin menu/link is shown.
3. Select `QA Delivery Org` tenant.
4. Verify access and data on:
   - `/dashboard`
   - `/tickets`
   - `/projects`
   - `/releases`
5. Verify create/edit forms are usable (project/ticket/release forms render and submit paths are accessible).
6. Tenant persistence regression check:
   - Select `QA Delivery Org`.
   - Hard refresh on `/dashboard`, then open `/tickets` and `/releases`.
   - Expected: tenant remains selected after reload/navigation.

## Client (`qa_client`)

1. Login at `/login`.
2. Open tenant switcher:
   - Expected: `QA Client Org` and `QA Delivery Org` are selectable.
3. Validate dashboard/flows load under client tenant.
4. Verify ticket workflow pages load:
   - `/dashboard`
   - `/tickets`
5. Tenant persistence regression check:
   - Select `QA Delivery Org` (or `QA Client Org`).
   - Hard refresh on `/dashboard`, then open `/tickets`.
   - Expected: chosen tenant remains selected.

## 4) Mobile Viewport QA

In browser devtools/emulation (or integrated browser viewport):

- Set viewport to `390 x 844`.
- Repeat for PM and client users:
  - Login
  - Tenant selection
  - Dashboard
  - Tickets

Pass criteria:

- No broken layout or overlapping critical controls.
- Key navigation and form controls remain reachable.

## 5) Known Issues Observed During Latest QA Pass

1. `GET /api/v1/notifications/push/config/` and `GET /api/v1/notifications/devices/` can return `503` in local setup.
2. Intermittent refresh/auth churn can emit transient `401` logs during startup bursts before settling.
3. Admin page transitions can occasionally render previous view momentarily before updating.

These should be tracked as QA findings if reproducible in clean sessions.
