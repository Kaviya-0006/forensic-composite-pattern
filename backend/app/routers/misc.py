from fastapi import APIRouter, Depends

from ..services import activity_service, case_service, search_service
from .deps import current_user, get_repo

router = APIRouter(prefix="/api", tags=["search, activity, dashboard"], dependencies=[Depends(current_user)])


@router.get("/search")
def search(q: str = "", repo=Depends(get_repo)):
    return search_service.search(repo, q)


@router.get("/activity")
def activity(limit: int = 50, case_id: str = None, repo=Depends(get_repo)):
    return activity_service.list_activity(repo, limit, case_id)


@router.get("/dashboard/stats")
def stats(repo=Depends(get_repo)):
    return case_service.dashboard_stats(repo)
