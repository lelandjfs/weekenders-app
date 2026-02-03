"""
Weekender FastAPI Backend
==========================

REST API for the Weekender multi-agent system.
Exposes endpoints for searching weekend activities.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os

# Import the runner
from runner import run_all_agents, get_weekend_dates

app = FastAPI(
    title="Weekender API",
    description="Multi-agent weekend activity search",
    version="1.0.0"
)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://weekenderapp.xyz",
        "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    city: str
    weekend: str = "this"  # "this", "next", or custom dates
    start_date: Optional[str] = None  # YYYY-MM-DD for custom
    end_date: Optional[str] = None


class SearchResponse(BaseModel):
    city: str
    start_date: str
    end_date: str
    concerts: list
    dining: list
    events: list
    locations: list
    errors: list


@app.get("/")
async def root():
    return {"status": "ok", "service": "Weekender API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/search", response_model=SearchResponse)
async def search_weekend(request: SearchRequest):
    """
    Search for weekend activities in a city.

    - **city**: City name (e.g., "San Francisco", "Austin")
    - **weekend**: "this" for this weekend, "next" for next weekend
    """
    try:
        # Run the multi-agent pipeline
        results = run_all_agents(
            city=request.city,
            weekend=request.weekend
        )

        return SearchResponse(
            city=results["city"],
            start_date=results["start_date"],
            end_date=results["end_date"],
            concerts=results["concerts"],
            dining=results["dining"],
            events=results["events"],
            locations=results["locations"],
            errors=results["errors"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dates/{weekend}")
async def get_dates(weekend: str):
    """Get the date range for a weekend option."""
    start, end = get_weekend_dates(weekend)
    return {"start_date": start, "end_date": end}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
