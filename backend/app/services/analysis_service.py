import json
from datetime import datetime
from typing import Any, Dict

from ..composite import Evidence
from . import activity_service as activity
from .evidence_service import load_evidence, persist_state


def run_analysis(repo, evidence: Evidence, actor: str) -> Dict[str, Any]:
    """Client code: it holds an Evidence and calls analyze(). It never asks whether it is a Leaf or a group."""
    activity.log(repo, actor, "ANALYSIS_STARTED", f"{actor} started analysis of {evidence.name}", evidence.case_id, evidence.id)
    result = evidence.analyze(actor)
    persist_state(repo, evidence)
    result["summary"] = evidence.summary()
    result["descendant_count"] = evidence.descendant_count()
    repo.save_analysis({"evidence_id": evidence.id, "case_id": evidence.case_id, "status": result["status"],
                        "result_json": json.dumps(result, default=str), "created_at": datetime.now()})
    n = evidence.descendant_count()
    activity.log(repo, actor, "ANALYSIS_COMPLETED", f"{evidence.name} analyzed" + (f" recursively: {n} descendant objects processed" if n else ""), evidence.case_id, evidence.id)
    return result


def analyze_evidence(repo, evidence_id: str, actor: str) -> Dict[str, Any]:
    return run_analysis(repo, load_evidence(repo, evidence_id), actor)
