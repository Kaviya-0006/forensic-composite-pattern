from typing import Any, Dict, List

from . import activity_service as activity
from .evidence_service import load_evidence, persist_state


def get_custody(repo, evidence_id: str) -> List[Dict[str, Any]]:
    return load_evidence(repo, evidence_id).custody()      # a group aggregates its descendants' events


def add_custody(repo, evidence_id: str, data: Dict[str, Any], actor: str) -> Dict[str, Any]:
    node = load_evidence(repo, evidence_id)
    event = node.emit_custody(data["action"], actor, data.get("integrity_status", "INTACT"), data.get("details", ""))
    persist_state(repo, node)
    activity.log(repo, actor, "CUSTODY_UPDATED", f"Chain of custody updated for {node.name}: {data['action']}", node.case_id, node.id)
    return event
