import os
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.config import ENVIRONMENT
from app.database import engine, get_db
from app import models
from app.migrations import run_migrations
from app.auth import get_current_user
from app.templating import templates
from app.security import security_middleware
from app.services.executor import sandbox_info

from app.routers import (auth_router, problems_router, judge_router, dashboard_router, admin_router,
                         student_router, extensions_router, contests_router, learning_router, faculty_router)

run_migrations(engine)      # create new tables + add new columns to an existing DB (idempotent, non-destructive)

app = FastAPI(title="CodeJudge AI - Online Judge & Learning Platform", docs_url=None, redoc_url=None)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

for r in (auth_router, problems_router, judge_router, dashboard_router, admin_router, student_router,
          extensions_router, contests_router, learning_router, faculty_router):
    app.include_router(r.router)

app.middleware("http")(security_middleware)


@app.middleware("http")
async def no_store_middleware(request: Request, call_next):
    response = await call_next(request)
    if isinstance(response, Response):
        ct = response.headers.get("content-type", "")
        if "text/html" in ct or response.headers.get("location"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
    return response


def _wants_json(request: Request) -> bool:
    p = request.url.path
    return p.startswith(("/api/", "/ai/", "/judge/", "/extensions/search", "/extensions/detect")) \
        or "application/json" in request.headers.get("accept", "") and "text/html" not in request.headers.get("accept", "")


@app.exception_handler(StarletteHTTPException)
async def http_exc_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code in (301, 302, 303, 307) and exc.headers and "Location" in exc.headers:
        return RedirectResponse(exc.headers["Location"], status_code=303)
    if _wants_json(request):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        user = get_current_user(request, db)
        titles = {401: "Please sign in", 403: "Access denied", 404: "Page not found", 413: "Too large", 422: "Invalid input", 429: "Slow down"}
        resp = templates.TemplateResponse("error.html", {
            "request": request, "user": user, "code": exc.status_code,
            "title": titles.get(exc.status_code, "Something went wrong"), "detail": exc.detail,
        }, status_code=exc.status_code)
        return resp
    finally:
        db.close()


@app.exception_handler(Exception)
async def unhandled_exc_handler(request: Request, exc: Exception):
    """Log the full traceback to the terminal and show a friendly page instead of a bare 'Internal Server Error'."""
    import traceback, logging
    tb = traceback.format_exc()
    logging.getLogger("uvicorn.error").error("Unhandled error on %s %s\n%s", request.method, request.url.path, tb)
    detail = "An unexpected error occurred. Please try again."
    if ENVIRONMENT != "production":
        detail = f"{type(exc).__name__}: {exc}"
    if _wants_json(request):
        return JSONResponse({"detail": detail}, status_code=500)
    try:
        return templates.TemplateResponse("error.html", {
            "request": request, "user": None, "code": 500, "title": "Something went wrong", "detail": detail,
        }, status_code=500)
    except Exception:
        return Response("Internal Server Error", status_code=500, media_type="text/plain")


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    msg = "; ".join(f"{'.'.join(str(x) for x in e['loc'][1:])}: {e['msg']}" for e in exc.errors())[:300]
    return await http_exc_handler(request, StarletteHTTPException(status_code=422, detail=f"Invalid input - {msg}"))


@app.get("/", response_class=HTMLResponse)
def home_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse("index.html", {
        "request": request, "user": user,
        "problem_count": db.query(models.Problem).filter(models.Problem.is_published == True).count(),  # noqa: E712
        "user_count": db.query(models.User).count(),
        "submission_count": db.query(models.Submission).count(),
        "top_problems": db.query(models.Problem).filter(models.Problem.is_published == True).order_by(models.Problem.id).limit(6).all(),  # noqa: E712
    })


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(models.User.__table__.select().limit(1))
    return {"status": "ok", "sandbox": sandbox_info()}
