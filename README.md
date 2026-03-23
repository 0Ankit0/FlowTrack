# Flowtrack

Flowtrack is an internal project management and external ticketing platform built on FastAPI, Next.js, and Flutter. The current implementation adds the first backend MVP for multi-tenant ticket intake, assignment workflows, project planning, milestone tracking, SLA policies, reporting, and audit history.

## What Exists Now

- System design documentation in [docs/system-design/README.md](/Users/ankit/Projects/Python/fastapi/flowtrack/docs/system-design/README.md)
- Existing platform modules for auth, multi-tenancy, notifications, analytics, finance, and observability
- New Flowtrack backend APIs for:
  - tickets, comments, attachments, and assignment history
  - projects, milestones, and tasks
  - operational summaries, SLA policy administration, and audit logs
- Seeded Flowtrack roles and default SLA policies at startup

## Backend Scope

- External client users can create and track tickets within their organization
- Internal users can triage, assign, update, and close tickets based on role
- Project managers can create projects, plan milestones, and link delivery work
- Milestones cannot be completed while linked tickets remain open
- Every mutation records an audit entry

## Quick Start

1. Review [docs/system-design/README.md](/Users/ankit/Projects/Python/fastapi/flowtrack/docs/system-design/README.md).
2. Copy [backend/.env.example](/Users/ankit/Projects/Python/fastapi/flowtrack/backend/.env.example) to `backend/.env`.
3. From `backend/`, install dependencies with `uv sync --group test`.
4. Start the API with `uv run uvicorn src.main:app --reload`.
5. Open `/docs` and use the `/api/v1/tickets`, `/api/v1/projects`, `/api/v1/reports/operational-summary`, `/api/v1/audit-logs`, and `/api/v1/admin/sla-policies/{policy_id}` endpoints.

## Verification

- General API smoke test: `cd backend && uv run --group test pytest tests/integration/api/test_general.py -q`
- Flowtrack integration tests: `cd backend && uv run --group test pytest tests/integration/flowtrack/test_flowtrack_api.py -q`
- Flowtrack workflow unit tests: `cd backend && uv run --group test pytest tests/unit/flowtrack/test_workflow.py -q`
