from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
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

# Stores request timestamps per client
client_requests = {}

# -----------------------------
# Middleware 1 - Request Context
# -----------------------------

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        request_id = request.headers.get("X-Request-ID")

        if not request_id:
            request_id = str(uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response


app.add_middleware(RequestContextMiddleware)

# -----------------------------
# Middleware 2 - CORS
# -----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# -----------------------------
# Middleware 3 - Rate Limiter
# -----------------------------

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        # Don't rate-limit CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        client_id = request.headers.get("X-Client-Id", "anonymous")

        now = time.time()

        if client_id not in client_requests:
            client_requests[client_id] = []

        # Remove expired timestamps
        client_requests[client_id] = [
            t for t in client_requests[client_id]
            if now - t < WINDOW
        ]

        if len(client_requests[client_id]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )

        client_requests[client_id].append(now)

        return await call_next(request)


app.add_middleware(RateLimitMiddleware)

# -----------------------------
# Endpoint
# -----------------------------

@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }


# Optional root endpoint
@app.get("/")
async def root():
    return {"message": "FastAPI middleware service is running"}