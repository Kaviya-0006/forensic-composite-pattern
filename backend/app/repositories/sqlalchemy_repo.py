from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models.orm import (ActivityLogModel, AnalysisResultModel, CaseModel, CustodyEventModel, EvidenceGroupModel, EvidenceModel)

EV_COLS = ("id", "case_id", "parent_id", "name", "type", "kind", "status", "description", "hash", "file_size", "source_device",
           "collected_by", "collected_at", "created_at", "updated_at")
CASE_COLS = ("id", "name", "description", "investigator", "priority", "status", "created_at", "updated_at")


def _dict(obj, cols) -> Dict[str, Any]:
    return {c: getattr(obj, c) for c in cols}


class SqlAlchemyRepository:
    """Persistence only. Returns plain dicts; hierarchy rules live in the Composite domain."""

    def __init__(self, db: Session):
        self.db = db

    # cases
    def count_cases(self) -> int: return self.db.query(CaseModel).count()
    def list_cases(self): return [_dict(c, CASE_COLS) for c in self.db.query(CaseModel).order_by(CaseModel.id)]

    def get_case(self, id: str) -> Optional[Dict[str, Any]]:
        c = self.db.get(CaseModel, id)
        return _dict(c, CASE_COLS) if c else None

    def create_case(self, d: Dict[str, Any]) -> None:
        self.db.add(CaseModel(**d)); self.db.flush()

    def update_case(self, id: str, **fields) -> None:
        c = self.db.get(CaseModel, id)
        for k, v in fields.items(): setattr(c, k, v)
        c.updated_at = datetime.now(); self.db.flush()

    def delete_case(self, id: str) -> None:
        ids = [r[0] for r in self.db.query(EvidenceModel.id).filter(EvidenceModel.case_id == id)]
        self.delete_evidence(ids)
        self.db.query(CaseModel).filter(CaseModel.id == id).delete(synchronize_session=False); self.db.flush()

    # evidence
    def evidence_rows(self, case_id: str) -> List[Dict[str, Any]]:
        q = self.db.query(EvidenceModel).filter(EvidenceModel.case_id == case_id).order_by(EvidenceModel.created_at, EvidenceModel.id)
        return [_dict(e, EV_COLS) for e in q]

    def get_evidence(self, id: str) -> Optional[Dict[str, Any]]:
        e = self.db.get(EvidenceModel, id)
        return _dict(e, EV_COLS) if e else None

    def insert_evidence(self, d: Dict[str, Any]) -> None:
        self.db.add(EvidenceModel(**{k: d.get(k) for k in EV_COLS})); self.db.flush()
        if d["kind"] == "group":
            self.db.add(EvidenceGroupModel(evidence_id=d["id"], group_type=d["type"])); self.db.flush()

    def update_evidence(self, id: str, **fields) -> None:
        e = self.db.get(EvidenceModel, id)
        for k, v in fields.items(): setattr(e, k, v)
        e.updated_at = datetime.now(); self.db.flush()

    def delete_evidence(self, ids: List[str]) -> None:
        if not ids: return
        for model in (CustodyEventModel, AnalysisResultModel, EvidenceGroupModel):
            col = model.evidence_id
            self.db.query(model).filter(col.in_(ids)).delete(synchronize_session=False)
        self.db.query(EvidenceModel).filter(EvidenceModel.id.in_(ids)).delete(synchronize_session=False); self.db.flush()

    # custody / analysis / activity
    def custody_rows(self, case_id: str):
        q = self.db.query(CustodyEventModel).filter(CustodyEventModel.case_id == case_id).order_by(CustodyEventModel.occurred_at, CustodyEventModel.id)
        return [_dict(c, ("id", "evidence_id", "action", "actor", "integrity_status", "details", "occurred_at")) for c in q]

    def add_custody(self, e: Dict[str, Any]) -> None:
        case_id = self.db.get(EvidenceModel, e["evidence_id"]).case_id
        self.db.add(CustodyEventModel(evidence_id=e["evidence_id"], case_id=case_id, action=e["action"], actor=e["actor"],
                                      integrity_status=e["integrity"], details=e["details"], occurred_at=e["occurred_at"])); self.db.flush()

    def save_analysis(self, d: Dict[str, Any]) -> None:
        self.db.add(AnalysisResultModel(**d)); self.db.flush()

    def add_activity(self, d: Dict[str, Any]) -> None:
        self.db.add(ActivityLogModel(**d)); self.db.flush()

    def list_activity(self, limit: int = 50, case_id: Optional[str] = None):
        q = self.db.query(ActivityLogModel)
        if case_id: q = q.filter(ActivityLogModel.case_id == case_id)
        return [_dict(a, ("id", "case_id", "actor", "action", "entity_id", "message", "created_at"))
                for a in q.order_by(ActivityLogModel.created_at.desc(), ActivityLogModel.id.desc()).limit(limit)]

    # search + ids
    def search_evidence(self, q: str, limit: int = 20):
        like = f"%{q}%"
        cols = (EvidenceModel.id, EvidenceModel.case_id, EvidenceModel.name, EvidenceModel.type, EvidenceModel.hash, EvidenceModel.source_device)
        rows = self.db.query(EvidenceModel).filter(or_(*[c.ilike(like) for c in cols])).order_by(EvidenceModel.case_id, EvidenceModel.created_at).limit(limit)
        return [_dict(e, EV_COLS) for e in rows]

    def _next(self, prefix: str, width: int, start: int) -> str:
        top = self.db.query(func.max(EvidenceModel.id)).filter(EvidenceModel.id.like(prefix + "%")).scalar()
        if prefix.startswith("CASE"):
            top = self.db.query(func.max(CaseModel.id)).filter(CaseModel.id.like(prefix + "%")).scalar()
        n = int(top[len(prefix):]) + 1 if top and top[len(prefix):].isdigit() else start
        return f"{prefix}{max(n, start):0{width}d}"

    def next_evidence_id(self) -> str: return self._next("EV-2026-", 5, 440)
    def next_group_id(self) -> str: return self._next("EV-GROUP-", 3, 1)
    def next_case_id(self) -> str: return self._next("CASE-2026-", 3, 1)
