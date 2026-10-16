from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text

from ..database import Base


class CaseModel(Base):
    __tablename__ = "cases"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    investigator = Column(String, default="")
    priority = Column(String, default="MEDIUM")
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


class EvidenceModel(Base):
    """One row per Evidence object. parent_id links a child to its Composite; root case groups have parent_id NULL."""
    __tablename__ = "evidence"
    __table_args__ = (CheckConstraint("parent_id IS NULL OR parent_id <> id", name="ck_not_own_parent"),
                      CheckConstraint("kind IN ('group','leaf')", name="ck_kind"))
    id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(String, ForeignKey("evidence.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    kind = Column(String, nullable=False)
    status = Column(String, default="PENDING")
    description = Column(Text, default="")
    hash = Column(String, default="")
    file_size = Column(String, default="")
    source_device = Column(String, default="")
    collected_by = Column(String, default="")
    collected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


class EvidenceGroupModel(Base):
    __tablename__ = "evidence_groups"
    evidence_id = Column(String, ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True)
    group_type = Column(String, nullable=False)


class CustodyEventModel(Base):
    __tablename__ = "chain_of_custody_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    evidence_id = Column(String, ForeignKey("evidence.id", ondelete="CASCADE"), index=True, nullable=False)
    case_id = Column(String, index=True)
    action = Column(String, nullable=False)
    actor = Column(String, default="")
    integrity_status = Column(String, default="INTACT")
    details = Column(Text, default="")
    occurred_at = Column(DateTime, default=datetime.now)


class AnalysisResultModel(Base):
    __tablename__ = "analysis_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    evidence_id = Column(String, ForeignKey("evidence.id", ondelete="CASCADE"), index=True, nullable=False)
    case_id = Column(String, index=True)
    status = Column(String, default="COMPLETED")
    result_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.now)


class ActivityLogModel(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, index=True, nullable=True)
    actor = Column(String, default="")
    action = Column(String, default="")
    entity_id = Column(String, nullable=True)
    message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
