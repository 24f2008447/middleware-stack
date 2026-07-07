from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import time

app = FastAPI()

EMAIL = "24f2008447@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = [
    "https://dash-26kvxf.example.com"
]

# -----------------------------
# CORS
# -----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# -----------------------------
# Request ID + Process Time
# -----------------------------

@app.middleware("http")
async def add_headers(request: Request, call_next):

    request_id = str(uuid4())

    start = time.perf_counter()

    response = await call_next(request)

    process_time = time.perf_counter() - start

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.6f}"

    return response

# -----------------------------
# Stats Endpoint
# -----------------------------

@app.get("/stats")
async def stats(values: str = Query(...)):

    nums = [int(v.strip()) for v in values.split(",")]

    total = sum(nums)
    count = len(nums)

    return {
        "email": EMAIL,
        "count": count,
        "sum": total,
        "min": min(nums),
        "max": max(nums),
        "mean": total / count
    }

# -----------------------------
# Root
# -----------------------------

@app.get("/")
async def root():
    return {
        "message": "Metrics API Running"
    }