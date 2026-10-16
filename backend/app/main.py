from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .composite import HierarchyError
from .database import SessionLocal, init_db
from .repositories.sqlalchemy_repo import SqlAlchemyRepository
from .routers import auth, cases, evidence, misc
from .seed import seed
from .services.errors import AppError


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        if seed(SqlAlchemyRepository(db)):
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="FORENSICVAULT API", description="Digital evidence management. Evidence hierarchy modelled with the Composite pattern.", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(HierarchyError)
async def hierarchy_error(_: Request, exc: HierarchyError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})      # 400 invalid operation, 409 circular/duplicate


@app.exception_handler(AppError)
async def app_error(_: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})      # 400, 401, 404


@app.exception_handler(Exception)
async def unexpected(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Unexpected server error."})


for r in (auth.router, cases.router, evidence.router, misc.router):
    app.include_router(r)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
