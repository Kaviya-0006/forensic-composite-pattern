from fastapi import APIRouter, Depends

from ..schemas.schemas import LoginIn
from ..services import auth_service
from .deps import current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(body: LoginIn):
    return auth_service.login(body.username, body.password)


@router.get("/me")
def me(user=Depends(current_user)):
    return user
