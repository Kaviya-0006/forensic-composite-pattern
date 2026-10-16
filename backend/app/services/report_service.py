from datetime import datetime
from typing import Any, Dict

from .errors import BadRequestError
from .evidence_service import load_case_tree
from . import case_service

KINDS = {"investigation": "Investigation Report", "inventory": "Evidence Inventory", "analysis": "Analysis Summary", "custody": "Chain of Custody", "integrity": "Integrity Report"}


def build(repo, case_id: str, kind: str) -> Dict[str, Any]:
    if kind not in KINDS:
        raise BadRequestError(f"Unknown report '{kind}'. Use one of {list(KINDS)}.")
    case = case_service.get_case(repo, case_id)
    tree = load_case_tree(repo, case_id)
    leaves = [n for n in tree.walk() if not n.is_composite()]
    s = tree.summary()
    lines = []
    if kind == "investigation":
        lines = [f"Case: {case['id']} {case['name']}", f"Investigator: {case['investigator']}  Priority: {case['priority']}  Status: {case['status']}", "", "Evidence hierarchy:"]
        def walk(n, d=0):
            lines.append(f"{'  ' * d}{n.name} [{n.role}] {n.get_status()}")
            for c in n.get_children():
                walk(c, d + 1)
        walk(tree)
    elif kind == "inventory":
        lines = [f"{n.id}  {n.type:<16} {n.get_status():<9} {n.file_size:<8} {n.source_device}" for n in leaves]
    elif kind == "analysis":
        lines = [f"Evidence items: {s['items']}", f"Analyzed: {s['analyzed']}", f"Verified: {s['verified']}", f"Network indicators: {s['network']}", f"Suspicious artifacts: {s['suspicious']}"]
    elif kind == "custody":
        lines = [f"{e['occurred_at']:%d %b %Y %H:%M}  {e['evidence_id']}  {e['action']}  ({e['actor']})" for e in tree.custody()]
    else:
        lines = [f"{n.id}  SHA-256 {n.sha256[:16]}...{n.sha256[-6:]}  {n.get_status()}" for n in leaves]
    return {"kind": kind, "title": KINDS[kind], "case_id": case_id, "generated_at": datetime.now(), "summary": s, "lines": lines}
