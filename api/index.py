from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List


app = FastAPI()


EMAIL = "24f2008447@ds.study.iitm.ac.in"

API_KEY = "ak_hzn229get61gaphu6i16fcus"


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


class Event(BaseModel):
    user: str
    amount: float
    ts: int


class AnalyticsRequest(BaseModel):
    events: List[Event]


@app.post("/analytics")
async def analytics(
    request: AnalyticsRequest,
    x_api_key: str | None = Header(default=None)
):

    # Authentication
    if x_api_key != API_KEY:
        return JSONResponse(
            status_code=401,
            content={
                "detail": "Unauthorized"
            }
        )


    events = request.events


    total_events = len(events)


    users = set()

    revenue = 0.0

    user_revenue = {}


    for event in events:

        users.add(event.user)

        if event.amount > 0:

            revenue += event.amount

            if event.user not in user_revenue:
                user_revenue[event.user] = 0

            user_revenue[event.user] += event.amount


    top_user = None

    if user_revenue:
        top_user = max(
            user_revenue,
            key=user_revenue.get
        )


    return {
        "email": EMAIL,
        "total_events": total_events,
        "unique_users": len(users),
        "revenue": revenue,
        "top_user": top_user
    }


@app.get("/")
def root():
    return {
        "message": "Analytics API running"
    }