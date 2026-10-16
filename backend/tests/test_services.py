"""Runs without FastAPI/SQLAlchemy: python -m tests.test_services (from the backend folder)."""
import json

from app.composite import CircularHierarchyError, DuplicateChildError, InvalidHierarchyOperation
from app.repositories.memory_repo import MemoryRepository
from app.seed import seed
from app.services import analysis_service, case_service, custody_service, evidence_service as ev, search_service
from app.services.errors import NotFoundError

ME = "Kaviya J"
repo = MemoryRepository()
assert seed(repo) and not seed(repo)

# --- reconstruct the Composite tree from persisted parent_id rows
tree = ev.load_case_tree(repo, "CASE-2026-001")
assert tree.role == "COMPOSITE" and [c.name for c in tree.get_children()] == ["Computer Evidence", "Mobile Evidence", "Network Evidence"]
computer = tree.get_child(0)
assert computer.parent is tree and computer.get_child(3).name == "Forensic Collection" and computer.get_child(3).is_composite()
disk = ev.load_evidence(repo, "EV-2026-00421")
assert disk.name == "Disk Image" and disk.role == "LEAF" and disk.get_children() == []
assert [p.name for p in disk.path()][-2:] == ["Computer Evidence", "Disk Image"]

# --- the SAME service call analyses a Leaf, a Composite and the Case
r_leaf = analysis_service.analyze_evidence(repo, "EV-2026-00421", ME)
assert r_leaf["role"] == "LEAF" and r_leaf["children"] == [] and r_leaf["status"] == "COMPLETED" and "File-system scan" in r_leaf["steps"]
assert ev.load_evidence(repo, "EV-2026-00422").get_status() == "ANALYZED"            # already analyzed leaf untouched
assert ev.load_evidence(repo, "EV-2026-00423").get_status() == "PENDING"             # sibling NOT analyzed by leaf analysis
comp_id = computer.id
r_group = analysis_service.analyze_evidence(repo, comp_id, ME)
assert r_group["role"] == "COMPOSITE" and len(r_group["children"]) == 4
nested = [c for c in r_group["children"] if c["role"] == "COMPOSITE"][0]
assert nested["name"] == "Forensic Collection" and len(nested["children"]) == 2      # nested composite recursed
assert all(ev.load_evidence(repo, i).get_status() == "ANALYZED" for i in ("EV-2026-00423", "EV-2026-00424", "EV-2026-00425"))
assert ev.load_evidence(repo, "EV-2026-00426").get_status() == "VERIFIED"            # mobile untouched (Device Image was VERIFIED)
r_case = analysis_service.analyze_evidence(repo, "CASE-2026-001", ME)
assert r_case["summary"]["analyzed"] == r_case["summary"]["items"] == 11 and r_case["descendant_count"] == 15
assert ev.load_case_tree(repo, "CASE-2026-001").get_status() == "ANALYZED"
assert len(repo.analyses) == 3 and json.loads(repo.analyses[-1]["result_json"])["name"] == "Unauthorized Network Access"

# --- Leaf cannot have children (service + domain)
try: ev.create(repo, {"name": "X", "type": "Disk Image"}, ME, parent_id="EV-2026-00421"); raise SystemExit("leaf accepted a child")
except InvalidHierarchyOperation as e: assert e.status_code == 400
try: ev.load_evidence(repo, "EV-2026-00421").add(ev.load_evidence(repo, "EV-2026-00422")); raise SystemExit("leaf add worked")
except InvalidHierarchyOperation: pass

# --- create group / nested group / evidence, then analyze the case again
g = ev.create(repo, {"case_id": "CASE-2026-001", "parent_id": "EV-GROUP-003", "name": "Cloud Evidence", "type": "Custom Group"}, ME, kind="group")
g2 = ev.create(repo, {"name": "Archive", "type": "Forensic Collection"}, ME, parent_id=g["id"], kind="group")
new = ev.create(repo, {"name": "CCTV Frame", "type": "Other", "source_device": "Cam-3", "hash": "ab" * 32}, ME, parent_id=g2["id"])
assert new["parent_id"] == g2["id"] and new["path"][-3:] == ["Cloud Evidence", "Archive", "CCTV Frame"]
r2 = analysis_service.analyze_evidence(repo, "CASE-2026-001", ME)
assert r2["summary"]["items"] == 12 and r2["summary"]["analyzed"] == 12

# --- move: valid, then every forbidden case
moved = ev.move(repo, new["id"], "EV-GROUP-001", ME)
assert moved["parent_id"] == "EV-GROUP-001" and repo.get_evidence(new["id"])["parent_id"] == "EV-GROUP-001"
assert new["id"] not in [c.id for c in ev.load_evidence(repo, g2["id"]).get_children()]
for target, exc in [(g2["id"], CircularHierarchyError), (g["id"], CircularHierarchyError)]:
    try: ev.move(repo, g["id"], target, ME); raise SystemExit("cycle allowed")
    except CircularHierarchyError as e: assert e.status_code == 409
try: ev.move(repo, new["id"], "EV-GROUP-001", ME); raise SystemExit("duplicate allowed")
except DuplicateChildError as e: assert e.status_code == 409
try: ev.move(repo, new["id"], "EV-2026-00421", ME); raise SystemExit("moved into leaf")
except InvalidHierarchyOperation: pass
try: ev.move(repo, "CASE-2026-001", "EV-GROUP-001", ME); raise SystemExit("case moved")
except Exception as e: assert getattr(e, "status_code", 0) in (400, 409)
try: ev.move(repo, "EV-2026-00421", "EV-GROUP-008", ME); raise SystemExit("cross-case move")
except Exception as e: assert e.status_code == 400
try: ev.load_evidence(repo, "nope"); raise SystemExit("missing")
except NotFoundError as e: assert e.status_code == 404

# --- remove: promote keeps children, cascade removes subtree
ev.delete(repo, g["id"], ME, mode="promote")
assert repo.get_evidence(g["id"]) is None and repo.get_evidence(g2["id"])["parent_id"] == "EV-GROUP-003"
ev.delete(repo, g2["id"], ME, mode="cascade")
assert repo.get_evidence(g2["id"]) is None
try: ev.delete(repo, "CASE-2026-001", ME); raise SystemExit("case root deleted")
except Exception as e: assert e.status_code == 400

# --- verify (uniform), custody, activity, search, dashboard, reports, case CRUD
ev.verify(repo, "EV-GROUP-008", ME)
assert ev.load_evidence(repo, "EV-2026-00438").get_status() == "VERIFIED"
c = custody_service.get_custody(repo, "EV-2026-00421")
assert [e["action"] for e in c][:3] == ["Evidence collected", "SHA-256 generated", "Transferred to forensic laboratory"] and c[-1]["action"] == "Analysis completed"
assert len(custody_service.get_custody(repo, "EV-GROUP-001")) > len(c)             # group aggregates descendants
custody_service.add_custody(repo, "EV-2026-00421", {"action": "Released to court", "details": "Exhibit A"}, ME)
assert custody_service.get_custody(repo, "EV-2026-00421")[-1]["action"] == "Released to court"
acts = [a["action"] for a in repo.list_activity(100)]
assert {"ANALYSIS_STARTED", "ANALYSIS_COMPLETED", "EVIDENCE_ADDED", "GROUP_CREATED", "EVIDENCE_MOVED", "EVIDENCE_REMOVED", "CUSTODY_UPDATED"} <= set(acts)
hit = search_service.search(repo, "00421")[0]
assert hit["path"] == ["CASE-2026-001", "Computer Evidence", "Disk Image"] and hit["case_id"] == "CASE-2026-001"
assert search_service.search(repo, "suspect-pc-07") and search_service.search(repo, repo.get_evidence("EV-2026-00421")["hash"][:10])
stats = case_service.dashboard_stats(repo)
assert stats["total_cases"] == 4 and stats["total_evidence"] == 20
newcase = case_service.create_case(repo, {"name": "New Case", "investigator": ME, "priority": "HIGH"}, ME)
assert newcase["id"] == "CASE-2026-005" and ev.load_case_tree(repo, newcase["id"]).is_composite()
case_service.delete_case(repo, newcase["id"], ME)
assert repo.get_case(newcase["id"]) is None and not repo.evidence_rows(newcase["id"])
cases = case_service.list_cases(repo)
assert cases[0]["group_count"] == 4 and cases[0]["evidence_count"] == 12
print("All backend domain + service tests passed (%d activity records)" % len(repo.activity))
