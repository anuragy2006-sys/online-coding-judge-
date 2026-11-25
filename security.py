"""Rate limiting + CSRF (Origin/Referer) protection + security headers."""
import time
import threading
from collections import defaultdict, deque
from urllib.parse import urlparse

from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app.config import RATE_LIMITS

_lock = threading.Lock()
_hits = defaultdict(deque)   # (bucket, ip) -> timestamps


def client_ip(request: Request) -> str:
    # Behind a reverse proxy (nginx) the real IP arrives in X-Forwarded-For.
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(bucket: str, ip: str):
    """Returns (allowed, retry_after_seconds)."""
    limit, window = RATE_LIMITS.get(bucket, RATE_LIMITS["default"])
    now = time.monotonic()
    with _lock:
        q = _hits[(bucket, ip)]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            return False, int(window - (now - q[0])) + 1
        q.append(now)
        return True, 0


def reset_rate_limits():
    with _lock:
        _hits.clear()


def bucket_for(path: str, method: str) -> str:
    if path in ("/login", "/register") and method == "POST":
        return "auth"
    if path == "/judge/run" or path == "/api/run-custom":
        return "run"
    if path.endswith("/submit"):
        return "submit"
    if path.startswith("/ai/") or path.startswith("/api/tutor") or path.startswith("/api/hint"):
        return "ai"
    return "default"


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def origin_ok(request: Request) -> bool:
    """CSRF defence for cookie-authenticated unsafe requests: the Origin (or
    Referer) host must match the Host the request was sent to."""
    origin = request.headers.get("origin") or request.headers.get("referer")
    if not origin:
        # Non-browser clients (curl, tests) send neither; the session cookie is
        # SameSite=Lax so a cross-site browser request can't carry it anyway.
        return True
    try:
        return urlparse(origin).netloc == request.headers.get("host", "")
    except Exception:
        return False


async def security_middleware(request: Request, call_next):
    path, method = request.url.path, request.method
    if method not in SAFE_METHODS:
        if not origin_ok(request):
            return PlainTextResponse("Cross-site request blocked.", status_code=403)
        ok, retry = check_rate_limit(bucket_for(path, method), client_ip(request))
        if not ok:
            if "application/json" in request.headers.get("accept", "") or path.startswith(("/ai/", "/api/", "/judge/")):
                return JSONResponse({"detail": f"Too many requests. Try again in {retry}s."}, status_code=429,
                                    headers={"Retry-After": str(retry)})
            return PlainTextResponse(f"Too many requests. Try again in {retry}s.", status_code=429,
                                     headers={"Retry-After": str(retry)})
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    return response
