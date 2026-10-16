from datetime import datetime
from typing import Any, Dict, List

from . import activity_service as activity
from .errors import BadRequestError, NotFoundError
from .evidence_service import load_case_tree


def _out(repo, case: Dict[str, Any]) -> Dict[str, Any]:
    tree = load_case_tree(repo, case["id"])
    last = repo.list_activity(1, case["id"])
    return {**case, "evidence_count": tree.summary()["items"], "group_count": tree.group_count() - 1,
            "root_id": tree.id, "last_activity_at": last[0]["created_at"] if last else case["updated_at"]}


def list_cases(repo) -> List[Dict[str, Any]]:
    return [_out(repo, c) for c in repo.list_cases()]


def get_case(repo, case_id: str) -> Dict[str, Any]:
    case = repo.get_case(case_id)
    if case is None:
        raise NotFoundError(f"Case '{case_id}' not found.")
    return _out(repo, case)


def create_case(repo, data: Dict[str, Any], actor: str) -> Dict[str, Any]:
    if not data["name"].strip():
        raise BadRequestError("Case name is required.")
    case_id, now = repo.next_case_id(), datetime.now()
    repo.create_case({"id": case_id, "name": data["name"].strip(), "description": data.get("description", ""), "investigator": data.get("investigator") or actor,
                      "priority": data.get("priority", "MEDIUM"), "status": "ACTIVE", "created_at": now, "updated_at": now})
    repo.insert_evidence({"id": case_id, "case_id": case_id, "parent_id": None, "name": data["name"].strip(), "type": "Investigation Case", "kind": "group",
                          "status": "PENDING", "description": data.get("description", ""), "hash": "", "file_size": "", "source_device": "",
                          "collected_by": actor, "collected_at": now, "created_at": now, "updated_at": now})   # the case is the root Composite
    activity.log(repo, actor, "CASE_CREATED", f"{actor} created {case_id}: {data['name'].strip()}", case_id, case_id)
    return get_case(repo, case_id)


def update_case(repo, case_id: str, data: Dict[str, Any], actor: str) -> Dict[str, Any]:
    get_case(repo, case_id)
    fields = {k: v for k, v in data.items() if k in {"name", "description", "investigator", "priority", "status"} and v is not None}
    repo.update_case(case_id, **fields)
    if "name" in fields:
        repo.update_evidence(case_id, name=fields["name"])
    activity.log(repo, actor, "CASE_UPDATED", f"{actor} updated {case_id}", case_id, case_id)
    return get_case(repo, case_id)


def delete_case(repo, case_id: str, actor: str) -> Dict[str, Any]:
    get_case(repo, case_id)
    repo.delete_case(case_id)
    activity.log(repo, actor, "CASE_DELETED", f"{actor} deleted {case_id}", None, case_id)
    return {"deleted": case_id}


def dashboard_stats(repo) -> Dict[str, Any]:
    cases = repo.list_cases()
    total = {"items": 0, "analyzed": 0, "verified": 0, "flagged": 0}
    groups = 0
    for c in cases:
        tree = load_case_tree(repo, c["id"])
        s = tree.summary()
        for k in total:
            total[k] += s[k]
        groups += tree.group_count() - 1
    return {"active_cases": sum(1 for c in cases if c["status"] == "ACTIVE"), "total_cases": len(cases), "total_evidence": total["items"],
            "evidence_groups": groups, "pending_analysis": total["items"] - total["analyzed"], "verified_evidence": total["verified"],
            "integrity": {"verified": total["verified"] - total["analyzed"], "analyzed": total["analyzed"], "flagged": total["flagged"],
                          "pending": total["items"] - total["verified"] - total["flagged"]}}
