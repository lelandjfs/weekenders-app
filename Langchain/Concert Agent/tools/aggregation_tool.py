"""
Aggregation Tool
================

Uses Claude Haiku to parse, deduplicate, and format concert results.

This tool:
- Parses full web pages to extract concert details
- Deduplicates concerts from multiple sources
- Combines structured (Ticketmaster) and unstructured (web) data
- Returns clean, formatted concert list
"""

import json
from typing import List, Dict
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from context_router import SearchContext

# Import schemas from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schemas import Concert, ConcertResults

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

# API Key from environment
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")


def aggregate_concerts(
    ticketmaster_results: List[Dict],
    web_page_contents: List[str],
    context: SearchContext,
    start_date: str,
    end_date: str
) -> ConcertResults:
    """
    Use Claude Haiku to parse, deduplicate, and format concert results.

    This handles:
    1. Parsing full web pages to extract concert details
    2. Deduplicating concerts from multiple sources
    3. Formatting everything into clean JSON

    Args:
        ticketmaster_results: Structured results from Ticketmaster
        web_page_contents: Full page content from Tavily EXTRACT
        context: Search context
        start_date: ISO date
        end_date: ISO date

    Returns:
        ConcertResults with cleaned, deduplicated concerts

    Example:
        >>> tm_results = [{"name": "Artist", "venue": "Venue", ...}]
        >>> web_pages = ["SOURCE: url\n\nFull page content..."]
        >>> result = aggregate_concerts(tm_results, web_pages, context, "2025-01-10", "2025-01-17")
        >>> result.total_count
        25
    """

    # PRE-FILTER: Only send Ticketmaster concerts within date range to Claude
    # This prevents confusion - Claude shouldn't have to filter dates for structured data
    from datetime import datetime
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    filtered_tm = []
    for tm in ticketmaster_results:
        try:
            concert_date = datetime.fromisoformat(tm["date"])
            if start_dt <= concert_date <= end_dt:
                filtered_tm.append(tm)
        except:
            # If date parsing fails, include it anyway and let Claude handle it
            filtered_tm.append(tm)

    print(f"   → Pre-filtered Ticketmaster: {len(ticketmaster_results)} → {len(filtered_tm)} (within {start_date} to {end_date})")
    ticketmaster_results = filtered_tm

    # If no results at all, return empty
    if not ticketmaster_results and not web_page_contents:
        return ConcertResults(
            concerts=[],
            total_count=0,
            date_range=f"{start_date} to {end_date}",
            search_location=context.location_info.normalized_location,
            search_radius_miles=context.search_parameters.concert_radius_miles
        )

    llm = ChatAnthropic(
        model="claude-3-5-haiku-20241022",  # HAIKU - cheap and fast
        anthropic_api_key=CLAUDE_API_KEY,
        temperature=0,
        max_tokens=8000  # Haiku max is 8192, use 8000 to be safe
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an extraction engine whose ONLY job is to pull structured concert events from the text provided.

Follow ALL rules EXACTLY:

1. Extract EVERY concert from ALL sources provided:
   - Ticketmaster (structured JSON) - include EVERY ONE
   - Web pages (Songkick, Bandsintown) - parse and extract EVERY concert found
   - Large shows, small shows, local gigs, bar shows, club shows, festivals — ALL of them
   - DO NOT skip any source - you must extract from both Ticketmaster AND web pages

2. Only include concerts happening BETWEEN (inclusive):
   START DATE: {start_date}
   END DATE: {end_date}
   CRITICAL: Do NOT include concerts outside this date range. Verify each date.

3. Only include concerts located in or very near:
   LOCATION: {location}
   NOTE: Location matching should be flexible. "New York, NY", "Brooklyn, NY", "Manhattan, NY"
   are all valid for "New York City". "Austin, TX" matches "Austin, Texas, USA". Be inclusive.

4. For each event, extract these fields:
   - name: artist or headliner name
   - venue: venue name
   - date: YYYY-MM-DD format (REQUIRED - if no date visible, skip this concert)
   - time: "H:MM PM" or null
   - location: "City, State"
   - price_range: "$X-$Y" or null
   - url: event URL or null
   - source: "ticketmaster", "songkick", "bandsintown", or "web"
   - genre: genre name or null

5. If ANY field is missing in the text, set it to null — DO NOT guess or hallucinate.

6. Date Headers: If the text contains a date header above a list of events (common on Songkick/Bandsintown),
   apply that date to each event listed below it until the next date header appears.

7. NEVER summarize, NEVER skip events, NEVER include anything outside the date/location filters.

8. BOTH Ticketmaster AND Web Pages are EQUALLY IMPORTANT:
   - Ticketmaster data is PRE-FILTERED and structured - include EVERY ONE
   - Web pages contain indie/small venue shows - you MUST parse them and extract concerts
   - DO NOT skip web pages just because you have Ticketmaster data!
   - CRITICAL: Extract from BOTH sources, then deduplicate if needed
   - Example: If you get 41 Ticketmaster + 10 web page concerts, you should return ~45-50 total (after dedup)

9. Deduplicate: If same artist + venue + date appears multiple times, keep the one with most information.

10. OUTPUT FORMAT - Return ONLY valid JSON:
{{
  "concerts": [
    {{
      "name": "...",
      "venue": "...",
      "date": "YYYY-MM-DD",
      "time": "..." or null,
      "location": "...",
      "price_range": "..." or null,
      "url": "..." or null,
      "source": "...",
      "genre": "..." or null
    }}
  ]
}}

The output MUST be valid JSON. Do NOT include explanations, markdown, or any text outside the JSON."""),
        ("human", """Aggregate these concert results:

TICKETMASTER RESULTS (Structured):
{ticketmaster}

WEB PAGES TO PARSE (Full content from concert listing sites):
{web_pages}

Date range: {start_date} to {end_date}
Location: {location}

Parse the web pages for individual concerts, then combine with Ticketmaster data.
Return deduplicated, cleaned concerts as JSON array.""")
    ])

    chain = prompt | llm

    try:
        print(f"   → Processing {len(ticketmaster_results)} Ticketmaster results")
        print(f"   → Parsing {len(web_page_contents)} web pages")

        # DEBUG: Show what sources we're parsing
        if web_page_contents:
            print(f"   → Web page sources:")
            for page in web_page_contents[:5]:  # Show first 5
                source_line = page.split('\n')[0]
                print(f"      • {source_line[:80]}")

            # DEBUG: Save first web page for manual inspection
            if len(web_page_contents) > 0:
                with open("/tmp/first_web_page.txt", "w") as f:
                    f.write(web_page_contents[0])
                # Also save the full web pages input sent to Claude
                with open("/tmp/all_web_pages_sent.txt", "w") as f:
                    f.write("\n\n---PAGE BREAK---\n\n".join(web_page_contents[:5]))

        # Truncate web pages if too long (to avoid token limits)
        # Increase limit from 5000 to 10000 to capture more date info
        truncated_pages = []
        for page in web_page_contents:
            if len(page) > 10000:
                truncated_pages.append(page[:10000] + "\n\n[...truncated...]")
            else:
                truncated_pages.append(page)

        # TWO-PASS APPROACH: Parse web pages separately to ensure they're not ignored
        web_concerts = []
        if truncated_pages:
            print(f"   → First pass: Parsing web pages only...")
            web_response = chain.invoke({
                "ticketmaster": "[]",  # Empty - parse web pages only
                "web_pages": "\n\n---PAGE BREAK---\n\n".join(truncated_pages),
                "start_date": start_date,
                "end_date": end_date,
                "location": context.location_info.normalized_location
            })

            web_content = web_response.content.strip()
            # Remove markdown if present
            if web_content.startswith("```"):
                web_content = web_content.split("```")[1]
                if web_content.startswith("json"):
                    web_content = web_content[4:]
                web_content = web_content.strip()

            # Find JSON block
            json_start = web_content.find("{")
            if json_start > 0:
                web_content = web_content[json_start:]
            json_end = web_content.rfind("}")
            if json_end > 0:
                web_content = web_content[:json_end + 1]

            try:
                web_data = json.loads(web_content)
                web_concerts = web_data.get("concerts", [])
                print(f"   → Extracted {len(web_concerts)} concerts from web pages")
            except:
                print(f"   → Failed to parse web concerts")
                web_concerts = []

        # Now combine Ticketmaster with web concerts (simple merge, let Claude dedupe if needed)
        print(f"   → Combining {len(ticketmaster_results)} Ticketmaster + {len(web_concerts)} web concerts...")

        # Simple deduplication: same artist + venue + date
        seen = set()
        combined_concerts = []

        for concert in ticketmaster_results + web_concerts:
            key = (
                concert.get("name", "").lower(),
                concert.get("venue", "").lower(),
                concert.get("date", "")
            )
            if key not in seen:
                seen.add(key)
                combined_concerts.append(concert)

        print(f"   → After deduplication: {len(combined_concerts)} unique concerts")

        # No need for second pass - just return combined results
        content = json.dumps({"concerts": combined_concerts})

        # DEBUG: Save Claude response for inspection
        with open("/tmp/claude_aggregation_debug.json", "w") as f:
            f.write(content)

        # Remove markdown if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        # Claude sometimes adds explanatory text before JSON - find the JSON block
        # Look for the first { that starts the JSON
        json_start = content.find("{")
        if json_start > 0:
            content = content[json_start:]

        # Find the last } to end the JSON (in case there's trailing text)
        json_end = content.rfind("}")
        if json_end > 0:
            content = content[:json_end + 1]

        # Parse concerts
        data = json.loads(content)
        concerts_list = data.get("concerts", [])

        # Convert to Pydantic models
        concerts = [Concert(**c) for c in concerts_list]

        print(f"✅ Aggregation complete: {len(concerts)} unique concerts")

        return ConcertResults(
            concerts=concerts,
            total_count=len(concerts),
            date_range=f"{start_date} to {end_date}",
            search_location=context.location_info.normalized_location,
            search_radius_miles=context.search_parameters.concert_radius_miles
        )

    except Exception as e:
        print(f"❌ Aggregation error: {e}")
        if 'response' in locals():
            print(f"Response preview: {response.content[:500]}")

        # Fallback: just use Ticketmaster results
        concerts = [Concert(**r) for r in ticketmaster_results[:50]]

        return ConcertResults(
            concerts=concerts,
            total_count=len(concerts),
            date_range=f"{start_date} to {end_date}",
            search_location=context.location_info.normalized_location,
            search_radius_miles=context.search_parameters.concert_radius_miles
        )
