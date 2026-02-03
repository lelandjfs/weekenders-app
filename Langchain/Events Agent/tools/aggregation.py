"""
Aggregation Tool for LangChain Events Agent
=============================================

LangChain-compatible tool for aggregating and deduplicating event results.
Uses Claude Haiku to parse web pages and combine with Ticketmaster data.
"""

import json
import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY


class AggregationInput(BaseModel):
    """Input schema for event aggregation."""
    ticketmaster_results: List[Dict[str, Any]] = Field(
        description="Structured results from Ticketmaster"
    )
    web_page_contents: List[str] = Field(
        description="Raw page contents from web search"
    )
    city: str = Field(description="City name for context")
    start_date: str = Field(description="Start date for filtering")
    end_date: str = Field(description="End date for filtering")


@tool(args_schema=AggregationInput)
@traceable(name="aggregate_events_llm", run_type="chain")
def aggregate_events(
    ticketmaster_results: List[Dict[str, Any]],
    web_page_contents: List[str],
    city: str,
    start_date: str,
    end_date: str
) -> List[Dict[str, Any]]:
    """
    Aggregate event results from multiple sources.

    Uses Claude Haiku to parse web pages, then combines with
    Ticketmaster results and deduplicates.

    Args:
        ticketmaster_results: Structured results from Ticketmaster
        web_page_contents: Raw page contents from web search
        city: City name for context
        start_date: Start date for filtering
        end_date: End date for filtering

    Returns:
        Deduplicated, sorted list of events
    """
    all_events = []

    # Add Ticketmaster results directly (already structured)
    for e in ticketmaster_results:
        e["source"] = "ticketmaster"
        all_events.append(e)

    print(f"   → Starting with {len(ticketmaster_results)} Ticketmaster events")

    # Parse web pages with Claude Haiku
    if web_page_contents:
        web_events = _parse_web_pages(web_page_contents, city, start_date, end_date)
        all_events.extend(web_events)
        print(f"   → Added {len(web_events)} events from web sources")

    # Deduplicate
    unique_events = _deduplicate(all_events)
    print(f"   → After deduplication: {len(unique_events)} unique events")

    # Sort by date, then by name
    unique_events.sort(
        key=lambda x: (x.get("date") or "9999-99-99", x.get("name", "").lower())
    )

    return unique_events


def _parse_web_pages(
    web_pages: List[str],
    city: str,
    start_date: str,
    end_date: str
) -> List[Dict[str, Any]]:
    """Use Claude Haiku to parse event details from web pages."""
    llm = ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        anthropic_api_key=ANTHROPIC_API_KEY,
        temperature=0,
        max_tokens=8000
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an event extraction engine. Extract event information from the web page content provided.

Rules:
1. Extract EVERY event mentioned in the web pages
2. For each event, extract:
   - name: event name (REQUIRED)
   - venue: venue name or null
   - date: date in YYYY-MM-DD format or null
   - time: time in HH:MM format or null
   - location: city/address or null
   - category: type of event (Sports, Arts, Family, Festival, Comedy, etc.) or null
   - description: brief description (1-2 sentences) or null
   - price_range: ticket price range or null
   - url: event URL or null
   - source: which source mentioned this (eventbrite, timeout, or web)

3. If a field is missing, set it to null - DO NOT guess
4. Focus on events in {city} between {start_date} and {end_date}
5. Skip events that are clearly concerts/music performances (those go to Concert Agent)
6. Skip events clearly outside the date range

OUTPUT FORMAT - Return ONLY valid JSON:
{{
  "events": [
    {{"name": "...", "venue": null, "date": null, "time": null, "location": null, "category": null, "description": null, "price_range": null, "url": null, "source": "eventbrite"}}
  ]
}}"""),
        ("human", """Parse these web pages and extract all events in {city} between {start_date} and {end_date}:

{web_pages}

Return events as JSON.""")
    ])

    chain = prompt | llm

    try:
        # Truncate pages if too long
        truncated_pages = []
        for page in web_pages:
            if len(page) > 10000:
                truncated_pages.append(page[:10000] + "\n\n[...truncated...]")
            else:
                truncated_pages.append(page)

        print(f"   → Parsing {len(truncated_pages)} web pages with Claude Haiku...")

        response = chain.invoke({
            "web_pages": "\n\n---PAGE BREAK---\n\n".join(truncated_pages),
            "city": city,
            "start_date": start_date,
            "end_date": end_date
        })

        content = response.content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        # Find JSON block
        json_start = content.find("{")
        if json_start > 0:
            content = content[json_start:]
        json_end = content.rfind("}")
        if json_end > 0:
            content = content[:json_end + 1]

        data = json.loads(content)
        events = data.get("events", [])

        return events

    except Exception as e:
        print(f"   ⚠️ Error parsing web pages: {e}")
        return []


def _deduplicate(events: List[Dict]) -> List[Dict]:
    """Remove duplicate events based on name + venue similarity."""
    seen = {}
    unique = []

    for e in events:
        name = (e.get("name") or "").lower().strip()
        venue = (e.get("venue") or "").lower().strip()
        date = e.get("date") or ""

        # Create key from name + venue + date
        key = _normalize_key(name, venue, date)

        if key and key not in seen:
            seen[key] = e
            unique.append(e)
        elif key in seen:
            # Merge data if we have more info
            _merge_event_data(seen[key], e)

    return unique


def _normalize_key(name: str, venue: str, date: str) -> str:
    """Create a normalized key for deduplication."""
    # Remove special characters
    name = re.sub(r"[^\w\s]", "", name)
    venue = re.sub(r"[^\w\s]", "", venue)

    # Remove extra whitespace
    name = " ".join(name.split())
    venue = " ".join(venue.split())

    return f"{name}_{venue}_{date}".lower()


def _merge_event_data(existing: Dict, new: Dict):
    """Merge data from new record into existing, filling in nulls."""
    for key, value in new.items():
        if value is not None and existing.get(key) is None:
            existing[key] = value

    if new.get("description") and not existing.get("description"):
        existing["description"] = new["description"]
