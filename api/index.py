from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import time

app = FastAPI()

# -----------------------------
# Configuration
# -----------------------------

EMAIL = "24f2008447@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = [
    "https://app-wxigmf.example.com",
    "https://exam.sanand.workers.dev",
]

RATE_LIMIT = 14
WINDOW = 10  # seconds

client_requests = {}

# -----------------------------
# Middleware 1 - Request Context
# -----------------------------

@app.middleware("http")
async def request_context(request: Request, call_next):

    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# -----------------------------
# Middleware 2 - Rate Limiter
# -----------------------------

@app.middleware("http")
async def rate_limiter(request: Request, call_next):

    # Don't rate-limit CORS preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    timestamps = client_requests.get(client_id, [])

    timestamps = [t for t in timestamps if now - t < WINDOW]

    if len(timestamps) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

    timestamps.append(now)
    client_requests[client_id] = timestamps

    return await call_next(request)


# -----------------------------
# Middleware 3 - CORS
# (ADD LAST so it wraps everything)
# -----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# -----------------------------
# Endpoint
# -----------------------------

@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }


@app.get("/")
async def root():
    return {"message": "FastAPI middleware service is running"}