# FORENSICVAULT: Digital Evidence Intelligence

Full-stack digital forensics evidence management system. React + TypeScript frontend, FastAPI backend, SQLite database.
The evidence hierarchy is modelled with the **Composite design pattern in the backend domain layer** and persisted with `parent_id` links.

## Run

**Backend** (terminal 1)
```
cd backend
python -m venv venv
venv\Scripts\activate          # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload
```
The SQLite database (`backend/forensicvault.db`) is created and seeded automatically on first start. API docs: http://127.0.0.1:8000/docs (use *Authorize* with a token from `POST /api/auth/login`).

**Frontend** (terminal 2)
```
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 (Vite proxies `/api` to port 8000). Demo login: `kaviya` / `forensic123` (also `arjun`, `meera`).

**Tests** (no FastAPI/SQLAlchemy needed): `cd backend && python -m tests.test_services`

## Composite pattern map

| Role | Class (backend/app/composite) | Notes |
|------|-------------------------------|-------|
| Component | `Evidence` (`evidence.py`) | abstract: `analyze()`, `display()`, `get_children()`, `add()`, `remove()`, `verify()`, `summary()` |
| Leaf | `IndividualEvidence` (`individual_evidence.py`) + `DiskImage`, `BrowserHistory`, `SystemLog`, `MobileDeviceImage`, `MobileMessage`, `CallRecord`, `NetworkPCAP`, `FirewallLog`, `DNSLog` (`concrete_evidence.py`) | no children; `add()`/`remove()` raise 400 |
| Composite | `EvidenceGroup` (`evidence_group.py`) + `InvestigationCase`, `ComputerEvidenceGroup`, `MobileEvidenceGroup`, `NetworkEvidenceGroup`, `CustomEvidenceGroup` | stores children, keeps `parent` references, delegates recursively |
| Client | `services/*.py` (e.g. `analysis_service.run_analysis(repo, evidence: Evidence)`) | never checks leaf vs group |

Flow for `POST /api/evidence/{id}/analyze`: the service loads the case rows, `builder.build_tree()` rebuilds the Composite object tree from `parent_id`, finds the object by id, and calls `evidence.analyze()`. A Leaf analyzes itself; a group calls `analyze()` on each child (nested groups recurse). The same endpoint serves a Disk Image, a group and a whole case. Statuses and custody events are then persisted.

Hierarchy rules enforced in the domain (`EvidenceGroup.validate_add`): leaf cannot have children (400), no cycles / moving a group into itself or a descendant (409), no duplicate child (409), a case cannot become a child (400), no cross-case moves (400). SQLite triggers additionally refuse a child under a leaf row.

## Database tables
`cases`, `evidence` (id, case_id, parent_id, name, type, kind, status, description, hash, file_size, source_device, collected_by, collected_at, created_at, updated_at), `evidence_groups`, `chain_of_custody_events`, `analysis_results`, `activity_logs`.

## REST API
Auth: `POST /api/auth/login`, `GET /api/auth/me`. Cases: `GET/POST /api/cases`, `GET/PUT/DELETE /api/cases/{id}`, `GET /api/cases/{id}/evidence` (tree), `GET /api/cases/{id}/reports/{kind}`.
Evidence: `GET/PUT/DELETE /api/evidence/{id}` (`?mode=cascade|promote`), `POST /api/evidence`, `POST /api/evidence/groups`, `POST /api/evidence/{parent}/children`, `DELETE /api/evidence/{parent}/children/{child}`, `GET /api/evidence/{id}/children`, `PUT /api/evidence/{id}/move`, `POST /api/evidence/{id}/analyze` (and `/analyze-recursive`, an alias), `POST /api/evidence/{id}/verify`, `GET/POST /api/evidence/{id}/custody`.
Other: `GET /api/search?q=`, `GET /api/activity`, `GET /api/dashboard/stats`.

## Demo script
Open CASE-2026-001, select **Disk Image** and Analyze (only that item), select **Computer Evidence** and Analyze (same call, recursive including *Forensic Collection*), select the **case** and Analyze (whole tree). Then Create Group, Add Evidence, create a nested group and Analyze the case again. The **Architecture** button shows the selected object's class and pattern role.
