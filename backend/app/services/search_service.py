from typing import Any, Dict, List

from .evidence_service import load_case_tree


def search(repo, q: str, limit: int = 20) -> List[Dict[str, Any]]:
    q = q.strip()
    if not q:
        return []
    trees: Dict[str, Any] = {}
    out = []
    for row in repo.search_evidence(q, limit):
        tree = trees.get(row["case_id"]) or trees.setdefault(row["case_id"], load_case_tree(repo, row["case_id"]))
        node = tree.find(row["id"])
        out.append({"id": node.id, "name": node.name, "type": node.type, "role": node.role, "status": node.get_status(), "case_id": node.case_id,
                    "hash": node.sha256, "source_device": node.source_device, "parent_name": node.parent.name if node.parent else None,
                    "path": [p.name if p.parent else p.id for p in node.path()]})
    return out
