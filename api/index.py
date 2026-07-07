from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import base64
import time

app = FastAPI()

# ----------------------------------------------------
# Configuration
# ----------------------------------------------------

TOTAL_ORDERS = 46
RATE_LIMIT = 15
WINDOW = 10

orders_catalog = [
    {
        "id": i,
        "item": f"Item {i}"
    }
    for i in range(1, TOTAL_ORDERS + 1)
]

idempotency_store = {}
client_requests = {}

# ----------------------------------------------------
# CORS
# ----------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://exam.sanand.workers.dev",
        "https://app-wxigmf.example.com",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
)

# ----------------------------------------------------
# Rate Limiter
# ----------------------------------------------------

@app.middleware("http")
async def rate_limit(request: Request, call_next):

    if request.method == "OPTIONS":
        return await call_next(request)

    # Only rate-limit requests that provide X-Client-Id
    client_id = request.headers.get("X-Client-Id")

    if client_id is None:
        return await call_next(request)

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
            }
        )

        response.headers["Retry-After"] = str(retry_after)

        return response

    timestamps.append(now)

    client_requests[client_id] = timestamps

    return await call_next(request)

# ----------------------------------------------------
# POST /orders
# ----------------------------------------------------

@app.post("/orders", status_code=201)
async def create_order(
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):

    if idempotency_key in idempotency_store:

        return JSONResponse(
            status_code=201,
            content=idempotency_store[idempotency_key]
        )

    order = {
        "id": str(uuid4()),
        "status": "created"
    }

    idempotency_store[idempotency_key] = order

    return JSONResponse(
        status_code=201,
        content=order
    )

# ----------------------------------------------------
# GET /orders
# ----------------------------------------------------

@app.get("/orders")
async def get_orders(
    limit: int = 10,
    cursor: str = None
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

    items = orders_catalog[start:end]

    next_cursor = None

    if end < TOTAL_ORDERS:
        next_cursor = base64.urlsafe_b64encode(
            str(end).encode()
        ).decode()

    return {
        "items": items,
        "next_cursor": next_cursor
    }

# ----------------------------------------------------
# Root
# ----------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "Orders API Running"
    }