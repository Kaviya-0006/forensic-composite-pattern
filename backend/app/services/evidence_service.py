"""Application services. The client (this layer) works only with the Evidence abstraction."""
from datetime import datetime
from typing import Any, Dict, Optional

from ..composite import Evidence, build_tree, create_node
from ..composite.concrete_evidence import GROUP_TYPES
from . import activity_service as activity
from .errors import BadRequestError, NotFoundError

UPDATABLE = {"name", "description", "status", "hash", "file_size", "source_device", "collected_by"}
STATUSES = {"PENDING", "VERIFIED", "ANALYZED", "FLAGGED"}


def load_case_tree(repo, case_id: str) -> Evidence:
    rows = repo.evidence_rows(case_id)
    if not rows:
        raise NotFoundError(f"Case '{case_id}' not found.")
    return build_tree(rows, repo.custody_rows(case_id))


def load_evidence(repo, evidence_id: str) -> Evidence:
    row = repo.get_evidence(evidence_id)
    if row is None:
        raise NotFoundError(f"Evidence '{evidence_id}' not found.")
    return load_case_tree(repo, row["case_id"]).find(evidence_id)


def get_tree(repo, case_id: str) -> Dict[str, Any]:
    return load_case_tree(repo, case_id).to_tree()


def get_evidence(repo, evidence_id: str) -> Dict[str, Any]:
    node = load_evidence(repo, evidence_id)
    d = node.display()
    d["path"] = [p.name for p in node.path()]
    return d


def get_children(repo, evidence_id: str):
    return [c.display() for c in load_evidence(repo, evidence_id).get_children()]


def persist_state(repo, node: Evidence) -> None:
    """Write back statuses and new custody events for a node and everything below it."""
    for n in node.walk():
        repo.update_evidence(n.id, status=n.get_status())
        for event in n.pop_new_custody():
            repo.add_custody(event)


def create(repo, data: Dict[str, Any], actor: str, parent_id: Optional[str] = None, kind: str = "leaf") -> Dict[str, Any]:
    parent_id = parent_id or data.get("parent_id")
    case_id = data.get("case_id")
    if parent_id:
        prow = repo.get_evidence(parent_id)
        if prow is None:
            raise NotFoundError(f"Parent '{parent_id}' not found.")
        case_id = prow["case_id"]
    if not case_id:
        raise BadRequestError("Either case_id or parent_id is required.")
    root = load_case_tree(repo, case_id)
    parent = root.find(parent_id) if parent_id else root
    if kind == "group" and data["type"] not in GROUP_TYPES:
        raise BadRequestError(f"Group type must be one of {GROUP_TYPES}.")
    if data.get("status", "PENDING") not in STATUSES:
        raise BadRequestError("Invalid status.")
    new_id = repo.next_group_id() if kind == "group" else (data.get("id") or repo.next_evidence_id())
    if repo.get_evidence(new_id):
        raise BadRequestError(f"Evidence ID '{new_id}' already exists.")
    collected = data.get("collected_at")
    if isinstance(collected, str) and collected:
        collected = datetime.fromisoformat(collected)
    row = {"id": new_id, "case_id": case_id, "parent_id": parent.id, "name": data["name"].strip(), "type": data["type"], "kind": kind,
           "status": data.get("status", "PENDING"), "description": data.get("description", ""), "hash": data.get("hash", ""),
           "file_size": data.get("file_size", ""), "source_device": data.get("source_device", ""), "collected_by": data.get("collected_by") or actor,
           "collected_at": collected or datetime.now(), "created_at": datetime.now(), "updated_at": datetime.now()}
    node = create_node(row)
    parent.add(node)                       # polymorphic validation: a Leaf parent raises 400
    repo.insert_evidence(row)
    node.on_created(actor)
    persist_state(repo, node)
    activity.log(repo, actor, "GROUP_CREATED" if kind == "group" else "EVIDENCE_ADDED",
                 f"{actor} {'created group' if kind == 'group' else 'added'} {node.name} in {parent.name}", case_id, node.id)
    return get_evidence(repo, node.id)


def update(repo, evidence_id: str, data: Dict[str, Any], actor: str) -> Dict[str, Any]:
    node = load_evidence(repo, evidence_id)
    fields = {k: v for k, v in data.items() if k in UPDATABLE and v is not None}
    if fields.get("status") and fields["status"] not in STATUSES:
        raise BadRequestError("Invalid status.")
    if node.is_composite():
        fields.pop("status", None)         # group status is derived from its children
    repo.update_evidence(evidence_id, **fields)
    activity.log(repo, actor, "EVIDENCE_UPDATED", f"{actor} updated {node.name}", node.case_id, node.id)
    return get_evidence(repo, evidence_id)


def delete(repo, evidence_id: str, actor: str, mode: str = "cascade", expected_parent: Optional[str] = None) -> Dict[str, Any]:
    node = load_evidence(repo, evidence_id)
    if node.parent is None:
        raise BadRequestError("An investigation case root cannot be removed here; delete the case instead.")
    if expected_parent and node.parent.id != expected_parent:
        raise BadRequestError(f"'{node.name}' is not a child of '{expected_parent}'.")
    parent = node.parent
    if mode == "promote":
        moved = node.dissolve()
        for child in moved:
            repo.update_evidence(child.id, parent_id=child.parent.id)
        repo.delete_evidence([node.id])
    else:
        parent.remove(node)
        repo.delete_evidence([n.id for n in node.walk()])
    activity.log(repo, actor, "EVIDENCE_REMOVED", f"{actor} removed {node.name} from {parent.name}", node.case_id, node.id)
    return {"deleted": evidence_id, "mode": mode, "parent_id": parent.id}


def move(repo, evidence_id: str, new_parent_id: str, actor: str) -> Dict[str, Any]:
    node = load_evidence(repo, evidence_id)
    if repo.get_evidence(new_parent_id) is None:
        raise NotFoundError(f"Destination '{new_parent_id}' not found.")
    new_parent = node.root().find(new_parent_id)
    if new_parent is None:
        raise BadRequestError("Evidence cannot be moved to a different case.")
    old_parent = node.parent
    if old_parent is None:
        raise BadRequestError("An investigation case root cannot be moved.")
    new_parent.validate_add(node)          # circular / duplicate / leaf-parent checks BEFORE any change
    old_parent.remove(node)
    new_parent.add(node)
    repo.update_evidence(node.id, parent_id=new_parent.id)
    for n in node.walk():
        n.on_moved(actor, old_parent.name, new_parent.name)
        for event in n.pop_new_custody():
            repo.add_custody(event)
    activity.log(repo, actor, "EVIDENCE_MOVED", f"{node.name} moved from {old_parent.name} to {new_parent.name}", node.case_id, node.id)
    return get_evidence(repo, node.id)


def verify(repo, evidence_id: str, actor: str) -> Dict[str, Any]:
    node = load_evidence(repo, evidence_id)
    node.verify(actor)                     # same call for a Leaf or a Composite
    persist_state(repo, node)
    activity.log(repo, actor, "HASH_VERIFIED", f"{actor} verified hash for {node.name}", node.case_id, node.id)
    return get_evidence(repo, evidence_id)
