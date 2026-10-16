from fastapi import APIRouter, Depends

from ..schemas.schemas import CustodyIn, EvidenceIn, EvidenceUpdate, GroupIn, MoveIn
from ..services import analysis_service, custody_service, evidence_service as svc
from .deps import current_user, get_repo

router = APIRouter(prefix="/api/evidence", tags=["evidence"], dependencies=[Depends(current_user)])


@router.post("", status_code=201)
def create_evidence(body: EvidenceIn, repo=Depends(get_repo), user=Depends(current_user)):
    return svc.create(repo, body.model_dump(), user["name"])


@router.post("/groups", status_code=201)
def create_group(body: GroupIn, repo=Depends(get_repo), user=Depends(current_user)):
    return svc.create(repo, body.model_dump(), user["name"], kind="group")


@router.get("/{evidence_id}")
def get_evidence(evidence_id: str, repo=Depends(get_repo)):
    return svc.get_evidence(repo, evidence_id)


@router.put("/{evidence_id}")
def update_evidence(evidence_id: str, body: EvidenceUpdate, repo=Depends(get_repo), user=Depends(current_user)):
    return svc.update(repo, evidence_id, body.model_dump(), user["name"])


@router.delete("/{evidence_id}")
def delete_evidence(evidence_id: str, mode: str = "cascade", repo=Depends(get_repo), user=Depends(current_user)):
    return svc.delete(repo, evidence_id, user["name"], mode)


@router.get("/{evidence_id}/children")
def children(evidence_id: str, repo=Depends(get_repo)):
    return svc.get_children(repo, evidence_id)


@router.post("/{parent_id}/children", status_code=201)
def add_child(parent_id: str, body: EvidenceIn, repo=Depends(get_repo), user=Depends(current_user)):
    return svc.create(repo, body.model_dump(), user["name"], parent_id=parent_id)      # 400 if parent is a Leaf


@router.delete("/{parent_id}/children/{child_id}")
def remove_child(parent_id: str, child_id: str, mode: str = "cascade", repo=Depends(get_repo), user=Depends(current_user)):
    return svc.delete(repo, child_id, user["name"], mode, expected_parent=parent_id)


@router.put("/{evidence_id}/move")
def move(evidence_id: str, body: MoveIn, repo=Depends(get_repo), user=Depends(current_user)):
    return svc.move(repo, evidence_id, body.parent_id, user["name"])


@router.post("/{evidence_id}/verify")
def verify(evidence_id: str, repo=Depends(get_repo), user=Depends(current_user)):
    return svc.verify(repo, evidence_id, user["name"])


@router.post("/{evidence_id}/analyze")
def analyze(evidence_id: str, repo=Depends(get_repo), user=Depends(current_user)):
    """ONE endpoint for a Leaf, a group or a whole case: the domain object decides what analyze() means."""
    return analysis_service.analyze_evidence(repo, evidence_id, user["name"])


@router.post("/{evidence_id}/analyze-recursive")
def analyze_recursive(evidence_id: str, repo=Depends(get_repo), user=Depends(current_user)):
    return analysis_service.analyze_evidence(repo, evidence_id, user["name"])           # alias of /analyze


@router.get("/{evidence_id}/custody")
def get_custody(evidence_id: str, repo=Depends(get_repo)):
    return custody_service.get_custody(repo, evidence_id)


@router.post("/{evidence_id}/custody", status_code=201)
def add_custody(evidence_id: str, body: CustodyIn, repo=Depends(get_repo), user=Depends(current_user)):
    return custody_service.add_custody(repo, evidence_id, body.model_dump(), user["name"])
