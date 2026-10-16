"""In-memory repository with the same interface as SqlAlchemyRepository (used by tests and demos without a database)."""
import itertools
from datetime import datetime
from typing import Any, Dict, List, Optional


class MemoryRepository:
    def __init__(self):
        self.cases: Dict[str, Dict[str, Any]] = {}
        self.evidence: Dict[str, Dict[str, Any]] = {}
        self.custody: List[Dict[str, Any]] = []
        self.analyses: List[Dict[str, Any]] = []
        self.activity: List[Dict[str, Any]] = []
        self._seq = itertools.count(1)

    def count_cases(self): return len(self.cases)
    def list_cases(self): return sorted((dict(c) for c in self.cases.values()), key=lambda c: c["id"])
    def get_case(self, id): return dict(self.cases[id]) if id in self.cases else None
    def create_case(self, d): self.cases[d["id"]] = dict(d)
    def update_case(self, id, **f): self.cases[id].update(f, updated_at=datetime.now())

    def delete_case(self, id):
        self.delete_evidence([i for i, e in self.evidence.items() if e["case_id"] == id])
        self.cases.pop(id, None)

    def evidence_rows(self, case_id): return [dict(e) for e in sorted(self.evidence.values(), key=lambda e: (e["created_at"], e["id"])) if e["case_id"] == case_id]
    def get_evidence(self, id): return dict(self.evidence[id]) if id in self.evidence else None
    def insert_evidence(self, d): self.evidence[d["id"]] = dict(d)
    def update_evidence(self, id, **f): self.evidence[id].update(f, updated_at=datetime.now())

    def delete_evidence(self, ids):
        s = set(ids)
        for i in s: self.evidence.pop(i, None)
        self.custody = [c for c in self.custody if c["evidence_id"] not in s]
        self.analyses = [a for a in self.analyses if a["evidence_id"] not in s]

    def custody_rows(self, case_id):
        return [{"id": i, "evidence_id": c["evidence_id"], "action": c["action"], "actor": c["actor"], "integrity_status": c["integrity"],
                 "details": c["details"], "occurred_at": c["occurred_at"]} for i, c in enumerate(self.custody) if c.get("case_id") == case_id]

    def add_custody(self, e):
        self.custody.append({**e, "case_id": self.evidence[e["evidence_id"]]["case_id"]})

    def save_analysis(self, d): self.analyses.append(dict(d))
    def add_activity(self, d): self.activity.append({**d, "id": next(self._seq)})

    def list_activity(self, limit=50, case_id=None):
        rows = [a for a in self.activity if case_id is None or a["case_id"] == case_id]
        return sorted(rows, key=lambda a: (a["created_at"], a["id"]), reverse=True)[:limit]

    def search_evidence(self, q, limit=20):
        q = q.lower()
        hits = [e for e in self.evidence.values() if any(q in str(e.get(k) or "").lower() for k in ("id", "case_id", "name", "type", "hash", "source_device"))]
        return [dict(e) for e in sorted(hits, key=lambda e: (e["case_id"], e["created_at"]))[:limit]]

    def _next(self, prefix, width, start):
        nums = [int(i[len(prefix):]) for i in list(self.evidence) + list(self.cases) if i.startswith(prefix) and i[len(prefix):].isdigit()]
        return f"{prefix}{max(nums + [start - 1]) + 1:0{width}d}"

    def next_evidence_id(self): return self._next("EV-2026-", 5, 440)
    def next_group_id(self): return self._next("EV-GROUP-", 3, 1)
    def next_case_id(self): return self._next("CASE-2026-", 3, 1)
