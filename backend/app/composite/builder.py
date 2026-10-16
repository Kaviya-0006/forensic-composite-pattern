"""Rebuilds the in-memory Composite tree from persisted rows (parent_id links)."""
from typing import Any, Dict, Iterable

from .concrete_evidence import GROUP_CLASSES, LEAF_CLASSES, CustomEvidenceGroup, OtherEvidence
from .errors import InvalidHierarchyOperation
from .evidence import Evidence


def create_node(row: Dict[str, Any]) -> Evidence:
    kwargs = dict(id=row["id"], name=row["name"], type=row["type"], case_id=row["case_id"], status=row.get("status") or "PENDING",
                  description=row.get("description") or "", sha256=row.get("hash") or "", file_size=row.get("file_size") or "",
                  source_device=row.get("source_device") or "", collected_by=row.get("collected_by") or "", collected_at=row.get("collected_at"))
    if row["kind"] == "group":
        return GROUP_CLASSES.get(row["type"], CustomEvidenceGroup)(**kwargs)
    return LEAF_CLASSES.get(row["type"], OtherEvidence)(**kwargs)


def build_tree(rows: Iterable[Dict[str, Any]], custody_rows: Iterable[Dict[str, Any]] = ()) -> Evidence:
    rows = sorted(rows, key=lambda r: (r["created_at"], r["id"]))
    nodes = {r["id"]: create_node(r) for r in rows}
    roots = []
    for r in rows:
        if r["parent_id"] is None:
            roots.append(nodes[r["id"]])
        else:
            nodes[r["parent_id"]].add(nodes[r["id"]])          # Composite.add validates every link
    if len(roots) != 1:
        raise InvalidHierarchyOperation("A case must have exactly one root evidence group.")
    for c in custody_rows:
        node = nodes.get(c["evidence_id"])
        if node:
            node.record_custody({"evidence_id": c["evidence_id"], "evidence_name": node.name, "action": c["action"], "actor": c["actor"],
                                 "integrity": c["integrity_status"], "details": c.get("details") or "", "occurred_at": c["occurred_at"]})
    return roots[0]
