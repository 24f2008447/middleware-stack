from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4
import time

app = FastAPI()

# ----------------------------
# Configuration
# ----------------------------

EMAIL = "24f2008447@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = [
    "https://app-wxigmf.example.com",
    "https://exam.sanand.workers.dev",
]

RATE_LIMIT = 14
WINDOW = 10

client_requests = {}

# ----------------------------
# Middleware 1
# Request Context
# ----------------------------

class RequestContextMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        request_id = request.headers.get("X-Request-ID")

        if request_id is None:
            request_id = str(uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response


app.add_middleware(RequestContextMiddleware)

# ----------------------------
# Middleware 2
# CORS
# ----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ----------------------------
# Middleware 3
# Rate Limiter
# ----------------------------

class RateLimitMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        # Don't rate limit preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        client_id = request.headers.get("X-Client-Id", "anonymous")

        now = time.time()

        timestamps = client_requests.get(client_id, [])

        timestamps = [
            t for t in timestamps
            if now - t < WINDOW
        ]

        if len(timestamps) >= RATE_LIMIT:

            retry_after = max(
                1,
                int(WINDOW - (now - timestamps[0]))
            )

            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded"
                },
            )

            response.headers["Retry-After"] = str(retry_after)

            origin = request.headers.get("Origin")

            if origin in ALLOWED_ORIGINS:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Expose-Headers"] = "X-Request-ID"
                response.headers["Vary"] = "Origin"

            return response

        timestamps.append(now)

        client_requests[client_id] = timestamps

        return await call_next(request)


app.add_middleware(RateLimitMiddleware)

# ----------------------------
# Endpoint
# ----------------------------

@app.get("/ping")
async def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }


@app.get("/")
async def root():
    return {
        "message": "Middleware Stack API Running"
    }