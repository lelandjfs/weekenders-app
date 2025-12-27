"""
Aggregation Tool for LangChain
===============================

Uses Claude Haiku to parse, deduplicate, and format concert results.
LangChain-compatible with @tool decorator for LangSmith tracing.
"""

import json
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY

# Use environment variable from config
CLAUDE_API_KEY = ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")


class AggregationInput(BaseModel):
    """Input schema for concert aggregation."""
    ticketmaster_results: List[Dict[str, Any]] = Field(
        description="List of concerts from Ticketmaster"
    )
    web_page_contents: List[str] = Field(
        description="List of web page contents to parse"
    )
    start_date: str = Field(description="Start date for filtering (YYYY-MM-DD)")
    end_date: str = Field(description="End date for filtering (YYYY-MM-DD)")
    location: str = Field(
        default="",
        description="Location for filtering (e.g., 'San Francisco, California, USA')"
    )


def _filter_by_date(concerts: List[Dict], start_date: str, end_date: str) -> List[Dict]:
    """Filter concerts to only those within the date range."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return concerts

    filtered = []
    for concert in concerts:
        date_str = concert.get("date", "")
        if not date_str or date_str == "TBD":
            continue
        try:
            concert_date = datetime.strptime(date_str, "%Y-%m-%d")
            if start <= concert_date <= end:
                filtered.append(concert)
        except ValueError:
            continue

    return filtered


def _deduplicate(concerts: List[Dict]) -> List[Dict]:
    """Remove duplicate concerts based on artist + venue + date."""
    seen = set()
    unique = []

    for concert in concerts:
        key = (
            (concert.get("name") or "").lower().strip(),
            (concert.get("venue") or "").lower().strip(),
            concert.get("date") or ""
        )
        if key not in seen:
            seen.add(key)
            unique.append(concert)

    return unique


@tool(args_schema=AggregationInput)
def aggregate_concert_results(
    ticketmaster_results: List[Dict[str, Any]],
    web_page_contents: List[str],
    start_date: str,
    end_date: str,
    location: str = ""
) -> List[Dict[str, Any]]:
    """
    Use Claude Haiku to parse, deduplicate, and format concert results.

    Combines Ticketmaster API results with parsed web page content,
    filters by date range, and removes duplicates.

    Args:
        ticketmaster_results: Concerts from Ticketmaster API
        web_page_contents: Raw page contents from web search
        start_date: Filter start date (YYYY-MM-DD)
        end_date: Filter end date (YYYY-MM-DD)
        location: Location for filtering

    Returns:
        Deduplicated list of concert objects sorted by date
    """
    # Pre-filter Ticketmaster results by date
    filtered_tm = _filter_by_date(ticketmaster_results, start_date, end_date)
    print(f"   → Pre-filtered Ticketmaster: {len(ticketmaster_results)} → {len(filtered_tm)}")

    # If no web pages, just return Ticketmaster results
    if not web_page_contents:
        return sorted(filtered_tm, key=lambda x: x.get("date", "9999-99-99"))

    # Use Claude Haiku to parse web pages
    llm = ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        anthropic_api_key=CLAUDE_API_KEY,
        temperature=0,
        max_tokens=8000
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an extraction engine. Extract concert events from the web page content provided.

Rules:
1. Extract EVERY concert you find in the web pages
2. Only include concerts between {start_date} and {end_date} (inclusive)
3. For each concert, extract:
   - name: artist/headliner name
   - venue: venue name
   - date: YYYY-MM-DD format (REQUIRED)
   - time: "H:MM PM" or null
   - location: "City, State" or null
   - price_range: "$X-$Y" or null
   - url: event URL or null
   - source: "songkick", "bandsintown", "seatgeek", or "web"
   - genre: genre or null

4. If a field is missing, set it to null - DO NOT guess
5. Skip any concert without a clear date

OUTPUT FORMAT - Return ONLY valid JSON:
{{
  "concerts": [
    {{"name": "...", "venue": "...", "date": "YYYY-MM-DD", "time": null, "location": null, "price_range": null, "url": null, "source": "...", "genre": null}}
  ]
}}"""),
        ("human", """Parse these web pages and extract all concerts:

{web_pages}

Date range: {start_date} to {end_date}
Location: {location}

Return concerts as JSON.""")
    ])

    chain = prompt | llm

    try:
        # Truncate pages if too long
        truncated_pages = []
        for page in web_page_contents:
            if len(page) > 10000:
                truncated_pages.append(page[:10000] + "\n\n[...truncated...]")
            else:
                truncated_pages.append(page)

        print(f"   → Parsing {len(truncated_pages)} web pages with Claude Haiku...")

        response = chain.invoke({
            "web_pages": "\n\n---PAGE BREAK---\n\n".join(truncated_pages),
            "start_date": start_date,
            "end_date": end_date,
            "location": location
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
        web_concerts = data.get("concerts", [])
        print(f"   → Extracted {len(web_concerts)} concerts from web pages")

    except Exception as e:
        print(f"   → Error parsing web pages: {e}")
        web_concerts = []

    # Combine Ticketmaster + web concerts
    print(f"   → Combining {len(filtered_tm)} Ticketmaster + {len(web_concerts)} web concerts...")
    all_concerts = filtered_tm + web_concerts

    # Deduplicate
    unique_concerts = _deduplicate(all_concerts)
    print(f"   → After deduplication: {len(unique_concerts)} unique concerts")

    # Sort by date
    unique_concerts.sort(key=lambda x: x.get("date", "9999-99-99"))

    return unique_concerts
