"""
LangGraph Concert Agent
=======================

A ReAct-style agent using LangGraph's prebuilt patterns.
"""

import json
from typing import List, Dict, Any
from datetime import datetime, timedelta

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from config import ANTHROPIC_API_KEY, setup_langsmith
from tools import ALL_TOOLS


# =============================================================================
# System Prompt
# =============================================================================

SYSTEM_PROMPT = """You are a concert discovery agent. Find concerts in the specified city during the given dates.

You have these tools:
1. analyze_location - Get lat/long coordinates for a city. USE FIRST.
2. search_ticketmaster - Search Ticketmaster for mainstream concerts.
3. discover_venues - Find indie/small venue names.
4. search_web_concerts - Search Songkick, Bandsintown, SeatGeek.
5. aggregate_concerts - Combine and deduplicate all results. USE LAST.

WORKFLOW (follow this order):
1. analyze_location to get coordinates
2. search_ticketmaster with coordinates
3. discover_venues to find indie venues
4. search_web_concerts for indie shows
5. aggregate_concerts to combine everything

After aggregation, summarize the concerts found. Be concise.
"""


# =============================================================================
# Agent Setup
# =============================================================================

def get_model():
    """Get Claude model."""
    return ChatAnthropic(
        model="claude-sonnet-4-20250514",
        anthropic_api_key=ANTHROPIC_API_KEY,
        temperature=0,
        max_tokens=4096
    )


def create_concert_agent():
    """Create the ReAct agent."""
    model = get_model()
    return create_react_agent(model, ALL_TOOLS)


# =============================================================================
# Helper Functions
# =============================================================================

def get_weekend_dates(weekend: str = "next") -> tuple:
    """Get start and end dates for the weekend."""
    today = datetime.now()
    day_of_week = today.weekday()

    days_until_saturday = (5 - day_of_week) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7

    if weekend == "next" and day_of_week >= 3:
        days_until_saturday += 7

    target_saturday = today + timedelta(days=days_until_saturday)
    start_date = target_saturday - timedelta(days=2)  # Thursday
    end_date = target_saturday  # Saturday

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def extract_concerts_from_messages(messages) -> List[Dict[str, Any]]:
    """Extract concert data from tool call results in messages."""
    concerts = []

    for msg in messages:
        # Look for ToolMessage with aggregate_concerts results
        if hasattr(msg, 'name') and msg.name == 'aggregate_concerts':
            try:
                content = msg.content
                if isinstance(content, str):
                    data = json.loads(content)
                    if isinstance(data, list):
                        concerts = data
            except:
                pass

        # Also check for tool results in content
        if hasattr(msg, 'content') and isinstance(msg.content, str):
            if '"source":' in msg.content and '"venue":' in msg.content:
                try:
                    data = json.loads(msg.content)
                    if isinstance(data, list) and len(data) > 0:
                        if 'venue' in data[0] and 'name' in data[0]:
                            concerts = data
                except:
                    pass

    return concerts


# =============================================================================
# Main Run Function
# =============================================================================

def run_concert_agent(
    city: str,
    weekend: str = "next",
    start_date: str = None,
    end_date: str = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run the concert agent.

    Args:
        city: City to search
        weekend: "next" or "this"
        start_date: Override start date (YYYY-MM-DD)
        end_date: Override end date (YYYY-MM-DD)
        verbose: Print progress

    Returns:
        Dict with concerts and metadata
    """
    setup_langsmith("concert-graph-agent")

    if not start_date or not end_date:
        start_date, end_date = get_weekend_dates(weekend)

    if verbose:
        print(f"\n{'='*60}")
        print(f"LANGGRAPH CONCERT AGENT")
        print(f"{'='*60}")
        print(f"City: {city}")
        print(f"Dates: {start_date} to {end_date}")
        print(f"{'='*60}\n")

    # Create agent
    agent = create_concert_agent()

    # Build the prompt
    user_message = f"""Find concerts in {city} from {start_date} to {end_date}.

Follow the workflow:
1. First analyze_location for {city}
2. Then search_ticketmaster
3. Then discover_venues
4. Then search_web_concerts
5. Finally aggregate_concerts

Provide a summary when done."""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]

    # Run agent with recursion limit
    config = {"recursion_limit": 30}

    try:
        result = agent.invoke({"messages": messages}, config=config)

        # Extract concerts from result
        all_messages = result.get("messages", [])
        concerts = extract_concerts_from_messages(all_messages)

        # Get final AI response
        final_response = ""
        for msg in reversed(all_messages):
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                if not msg.content.startswith('[') and not msg.content.startswith('{'):
                    final_response = msg.content
                    break

        if verbose:
            print(f"\n{'='*60}")
            print("COMPLETE")
            print(f"{'='*60}")
            print(f"Concerts found: {len(concerts)}")

        return {
            "final_concerts": concerts,
            "summary": final_response,
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
        }

    except Exception as e:
        if verbose:
            print(f"Error: {e}")
        raise


if __name__ == "__main__":
    import sys
    city = sys.argv[1] if len(sys.argv) > 1 else "Austin, Texas"
    weekend = sys.argv[2] if len(sys.argv) > 2 else "next"
    result = run_concert_agent(city, weekend)
    print(f"\nFound {len(result.get('final_concerts', []))} concerts")
