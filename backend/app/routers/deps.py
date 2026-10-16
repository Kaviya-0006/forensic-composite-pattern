from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..database import SessionLocal
from ..repositories.sqlalchemy_repo import SqlAlchemyRepository
from ..services import auth_service

bearer = HTTPBearer(auto_error=False)


def get_repo():
    db = SessionLocal()
    try:
        yield SqlAlchemyRepository(db)
        db.commit()                      # one transaction per request; any exception skips the commit
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def current_user(cred: Optional[HTTPAuthorizationCredentials] = Depends(bearer)):
    return auth_service.user_for(cred.credentials if cred else None)
