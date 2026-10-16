from fastapi import APIRouter, Depends

from ..schemas.schemas import CaseIn, CaseUpdate
from ..services import case_service, evidence_service, report_service
from .deps import current_user, get_repo

router = APIRouter(prefix="/api", tags=["cases"], dependencies=[Depends(current_user)])


@router.get("/cases")
def list_cases(repo=Depends(get_repo)):
    return case_service.list_cases(repo)


@router.get("/cases/{case_id}")
def get_case(case_id: str, repo=Depends(get_repo)):
    return case_service.get_case(repo, case_id)


@router.post("/cases", status_code=201)
def create_case(body: CaseIn, repo=Depends(get_repo), user=Depends(current_user)):
    return case_service.create_case(repo, body.model_dump(), user["name"])


@router.put("/cases/{case_id}")
def update_case(case_id: str, body: CaseUpdate, repo=Depends(get_repo), user=Depends(current_user)):
    return case_service.update_case(repo, case_id, body.model_dump(), user["name"])


@router.delete("/cases/{case_id}")
def delete_case(case_id: str, repo=Depends(get_repo), user=Depends(current_user)):
    return case_service.delete_case(repo, case_id, user["name"])


@router.get("/cases/{case_id}/evidence")
def case_evidence_tree(case_id: str, repo=Depends(get_repo)):
    return evidence_service.get_tree(repo, case_id)         # the Composite tree, serialised recursively


@router.get("/cases/{case_id}/reports/{kind}")
def report(case_id: str, kind: str, repo=Depends(get_repo)):
    return report_service.build(repo, case_id, kind)
