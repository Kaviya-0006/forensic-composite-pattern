from typing import Optional

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str
    password: str


class CaseIn(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    investigator: Optional[str] = None
    priority: str = "MEDIUM"


class CaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    investigator: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class EvidenceIn(BaseModel):
    case_id: Optional[str] = None
    parent_id: Optional[str] = None
    id: Optional[str] = None
    name: str = Field(min_length=1)
    type: str = "Other"
    description: str = ""
    hash: str = ""
    file_size: str = ""
    source_device: str = ""
    collected_by: Optional[str] = None
    collected_at: Optional[str] = None
    status: str = "PENDING"


class GroupIn(BaseModel):
    case_id: Optional[str] = None
    parent_id: Optional[str] = None
    name: str = Field(min_length=1)
    type: str = "Custom Group"
    description: str = ""


class EvidenceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    hash: Optional[str] = None
    file_size: Optional[str] = None
    source_device: Optional[str] = None
    collected_by: Optional[str] = None


class MoveIn(BaseModel):
    parent_id: str


class CustodyIn(BaseModel):
    action: str = Field(min_length=1)
    details: str = ""
    integrity_status: str = "INTACT"
