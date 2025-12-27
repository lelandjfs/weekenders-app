"""
Weekenders API Backend
======================

FastAPI server that orchestrates all 4 agents in parallel.
Returns structured JSON output with LangSmith tracing.

Run with: uvicorn main:app --reload
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langsmith import traceable
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# Claude model for structured output
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Results storage folder
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Add Langchain folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Langchain"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Langchain", "Concert Agent"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Langchain", "Dining Agent"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Langchain", "Events Agent"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Langchain", "Locations Agent"))

# =============================================================================
# Pydantic Schemas for Structured Output
# =============================================================================

class SearchRequest(BaseModel):
    """User search request."""
    city: str = Field(description="City to search")
    weekend: str = Field(default="next", description="'this' or 'next' weekend")


class ResultItem(BaseModel):
    """Generic result item."""
    name: str
    category: Optional[str] = None
    venue: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    address: Optional[str] = None
    rating: Optional[float] = None
    price_range: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    source: str


class AgentResult(BaseModel):
    """Result from a single agent."""
    agent: str
    success: bool
    count: int = 0
    items: List[Dict[str, Any]] = []
    error: Optional[str] = None
    run_time_seconds: float = 0


class WeekendersResponse(BaseModel):
    """Complete structured response."""
    city: str
    date_range: Dict[str, str]
    concerts: AgentResult
    dining: AgentResult
    events: AgentResult
    locations: AgentResult
    formatted_output: str  # Claude-formatted readable output
    metadata: Dict[str, Any]


# =============================================================================
# Structured Output Processor (Claude)
# =============================================================================

STRUCTURED_OUTPUT_PROMPT = """You are formatting weekend trip results for a user.

Given the raw JSON results from 4 agents, create a clean, readable summary.

FORMAT RULES:
1. Group by section: 🎵 CONCERTS, 🍽️ DINING, 🎭 EVENTS, 📍 LOCATIONS
2. Each item on ONE line: Date | Name | Venue/Location
3. If no date, use "Ongoing" or skip the date field
4. Limit to top 10 items per section
5. Sort by date where applicable

RAW RESULTS:
{raw_results}

CITY: {city}
DATE RANGE: {date_range}

Output the formatted summary:"""


@traceable(name="format_structured_output")
def format_structured_output(city: str, date_range: str, concerts: AgentResult,
                             dining: AgentResult, events: AgentResult,
                             locations: AgentResult) -> str:
    """Use Claude to format raw results into readable structured output."""

    raw_results = {
        "concerts": {"count": concerts.count, "items": concerts.items[:15]},
        "dining": {"count": dining.count, "items": dining.items[:15]},
        "events": {"count": events.count, "items": events.items[:15]},
        "locations": {"count": locations.count, "items": locations.items[:15]},
    }

    try:
        llm = ChatAnthropic(
            model="claude-3-5-haiku-20241022",
            anthropic_api_key=ANTHROPIC_API_KEY,
            temperature=0,
            max_tokens=2000
        )

        prompt = ChatPromptTemplate.from_messages([
            ("human", STRUCTURED_OUTPUT_PROMPT)
        ])

        chain = prompt | llm
        response = chain.invoke({
            "raw_results": json.dumps(raw_results, indent=2),
            "city": city,
            "date_range": date_range
        })

        return response.content

    except Exception as e:
        # Fallback: simple formatting without Claude
        lines = [f"Weekend in {city} ({date_range})\n"]
        lines.append(f"🎵 CONCERTS ({concerts.count})")
        for item in concerts.items[:10]:
            lines.append(f"  {item.get('date', 'TBD')} | {item.get('name', 'Unknown')} | {item.get('venue', 'TBD')}")
        lines.append(f"\n🍽️ DINING ({dining.count})")
        for item in dining.items[:10]:
            lines.append(f"  {item.get('name', 'Unknown')} | {item.get('neighborhood', item.get('address', 'TBD'))}")
        lines.append(f"\n🎭 EVENTS ({events.count})")
        for item in events.items[:10]:
            lines.append(f"  {item.get('date', 'TBD')} | {item.get('name', 'Unknown')} | {item.get('venue', 'TBD')}")
        lines.append(f"\n📍 LOCATIONS ({locations.count})")
        for item in locations.items[:10]:
            lines.append(f"  {item.get('name', 'Unknown')} | {item.get('category', 'TBD')} | {item.get('address', 'TBD')}")
        return "\n".join(lines)


def save_results_json(city: str, data: dict) -> str:
    """Save raw JSON results to file for review."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    city_slug = city.lower().replace(" ", "_").replace(",", "")
    filename = f"{city_slug}_{timestamp}.json"
    filepath = os.path.join(RESULTS_DIR, filename)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)

    return filepath


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Weekenders API",
    description="Find concerts, dining, events, and locations for your weekend trip",
    version="1.0.0"
)

# Allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Agent Runners
# =============================================================================

def run_concert_agent(city: str, weekend: str) -> AgentResult:
    """Run concert agent and return structured result."""
    start_time = datetime.now()
    try:
        from concert_agent import ConcertAgent
        agent = ConcertAgent()
        result = agent.run(city, weekend=weekend)

        return AgentResult(
            agent="concerts",
            success=True,
            count=result.total_concerts,
            items=result.concerts,
            run_time_seconds=(datetime.now() - start_time).total_seconds()
        )
    except Exception as e:
        return AgentResult(
            agent="concerts",
            success=False,
            error=str(e),
            run_time_seconds=(datetime.now() - start_time).total_seconds()
        )


def run_dining_agent(city: str) -> AgentResult:
    """Run dining agent and return structured result."""
    start_time = datetime.now()
    try:
        from dining_agent import DiningAgent
        agent = DiningAgent()
        result = agent.run(city)

        return AgentResult(
            agent="dining",
            success=True,
            count=result.total_restaurants,
            items=result.restaurants,
            run_time_seconds=(datetime.now() - start_time).total_seconds()
        )
    except Exception as e:
        return AgentResult(
            agent="dining",
            success=False,
            error=str(e),
            run_time_seconds=(datetime.now() - start_time).total_seconds()
        )


def run_events_agent(city: str, weekend: str) -> AgentResult:
    """Run events agent and return structured result."""
    start_time = datetime.now()
    try:
        from test_agent import EventsAgent
        agent = EventsAgent()
        result = agent.run(city, weekend=weekend)

        return AgentResult(
            agent="events",
            success=True,
            count=result.total_events,
            items=result.events,
            run_time_seconds=(datetime.now() - start_time).total_seconds()
        )
    except Exception as e:
        return AgentResult(
            agent="events",
            success=False,
            error=str(e),
            run_time_seconds=(datetime.now() - start_time).total_seconds()
        )


def run_locations_agent(city: str) -> AgentResult:
    """Run locations agent and return structured result."""
    start_time = datetime.now()
    try:
        from test_agent import LocationsAgent
        agent = LocationsAgent()
        result = agent.run(city)

        return AgentResult(
            agent="locations",
            success=True,
            count=result.total_locations,
            items=result.locations,
            run_time_seconds=(datetime.now() - start_time).total_seconds()
        )
    except Exception as e:
        return AgentResult(
            agent="locations",
            success=False,
            error=str(e),
            run_time_seconds=(datetime.now() - start_time).total_seconds()
        )


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Weekenders API is running"}


@app.post("/search", response_model=WeekendersResponse)
@traceable(name="weekenders_search")
async def search(request: SearchRequest):
    """
    Search all agents in parallel for a city.

    Returns structured JSON with results from all 4 agents.
    """
    city = request.city
    weekend = request.weekend
    start_time = datetime.now()

    # Run all agents in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as executor:
        concert_future = executor.submit(run_concert_agent, city, weekend)
        dining_future = executor.submit(run_dining_agent, city)
        events_future = executor.submit(run_events_agent, city, weekend)
        locations_future = executor.submit(run_locations_agent, city)

        # Collect results
        concerts = concert_future.result()
        dining = dining_future.result()
        events = events_future.result()
        locations = locations_future.result()

    total_time = (datetime.now() - start_time).total_seconds()

    # Format date range
    date_range_str = "This Weekend"  # TODO: Get actual dates from agents

    # Use Claude to format structured output
    formatted_output = format_structured_output(
        city=city,
        date_range=date_range_str,
        concerts=concerts,
        dining=dining,
        events=events,
        locations=locations
    )

    # Build response
    response_data = {
        "city": city,
        "date_range": {"start": "TBD", "end": "TBD"},
        "concerts": concerts.model_dump(),
        "dining": dining.model_dump(),
        "events": events.model_dump(),
        "locations": locations.model_dump(),
        "formatted_output": formatted_output,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_results": concerts.count + dining.count + events.count + locations.count,
            "total_run_time_seconds": round(total_time, 2),
            "agents_run": ["concerts", "dining", "events", "locations"],
            "agents_succeeded": [
                a for a, r in [("concerts", concerts), ("dining", dining),
                               ("events", events), ("locations", locations)]
                if r.success
            ],
        }
    }

    # Save JSON for review
    saved_path = save_results_json(city, response_data)
    response_data["metadata"]["saved_to"] = saved_path

    return WeekendersResponse(**response_data)


@app.get("/search/{city}")
@traceable(name="weekenders_search_get")
async def search_get(city: str, weekend: str = "next"):
    """GET version of search for easy testing."""
    return await search(SearchRequest(city=city, weekend=weekend))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
