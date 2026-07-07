from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import time
import base64

app = FastAPI()

TOTAL_ORDERS = 46
RATE_LIMIT = 15
WINDOW = 10

ALLOWED_ORIGINS = {
    "https://exam.sanand.workers.dev",
    "https://app-wxigmf.example.com",
}

orders = [
    {"id": i, "item": f"Item {i}"}
    for i in range(1, TOTAL_ORDERS + 1)
]

idempotency_store = {}
client_requests = {}

# ---------- Rate Limiter ----------

@app.middleware("http")
async def rate_limit(request: Request, call_next):

    if request.method == "OPTIONS":
        return await call_next(request)

    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    bucket = client_requests.get(client_id, [])

    bucket = [t for t in bucket if now - t < WINDOW]

    if len(bucket) >= RATE_LIMIT:

        retry_after = max(
            1,
            int(WINDOW - (now - bucket[0]))
        )

        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

        response.headers["Retry-After"] = str(retry_after)

        origin = request.headers.get("Origin")

        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Expose-Headers"] = "Retry-After"

        return response

    bucket.append(now)

    client_requests[client_id] = bucket

    return await call_next(request)


# ---------- CORS ----------

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_ORIGINS),
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
)

# ---------- POST ----------

@app.post("/orders", status_code=201)
async def create_order(
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):

    if idempotency_key in idempotency_store:
        return idempotency_store[idempotency_key]

    order = {
        "id": str(uuid4()),
        "status": "created",
    }

    idempotency_store[idempotency_key] = order

    return order


# ---------- GET ----------

@app.get("/orders")
async def list_orders(
    limit: int = 10,
    cursor: str | None = None,
):

    start = 0

    if cursor:
        try:
            start = int(
                base64.urlsafe_b64decode(
                    cursor.encode()
                ).decode()
            )
        except Exception:
            start = 0

    end = min(start + limit, TOTAL_ORDERS)

    next_cursor = None

    if end < TOTAL_ORDERS:
        next_cursor = base64.urlsafe_b64encode(
            str(end).encode()
        ).decode()

    return {
        "items": orders[start:end],
        "next_cursor": next_cursor,
    }


@app.get("/")
async def root():
    return {"status": "running"}