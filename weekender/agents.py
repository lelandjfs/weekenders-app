"""
Weekender Agents
================

4 separate LangGraph agents for parallel execution:
- Concert Agent
- Dining Agent
- Events Agent
- Locations Agent

Each agent has its own context window and tools.
"""

import sys
import os

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from config import ANTHROPIC_API_KEY

# Path to Langchain agents folder
_langchain_dir = os.path.join(os.path.dirname(__file__), "..", "Langchain")


# =============================================================================
# Import ALL tools at module load time to avoid parallel import issues
# =============================================================================

def _import_all_tools():
    """Import all tools from all agents at once."""
    tools = {}

    # Save original state
    original_path = sys.path.copy()

    # --- Concert Agent ---
    sys.path = [p for p in original_path if 'weekender' not in p]
    sys.path.insert(0, os.path.join(_langchain_dir, "Concert Agent"))
    # Clear cached modules including config
    for mod in list(sys.modules.keys()):
        if mod.startswith('tools') or mod == 'config':
            del sys.modules[mod]

    from tools import search_ticketmaster
    tools['concert'] = [search_ticketmaster]

    # --- Dining Agent ---
    sys.path = [p for p in original_path if 'weekender' not in p]
    sys.path.insert(0, os.path.join(_langchain_dir, "Dining Agent"))
    for mod in list(sys.modules.keys()):
        if mod.startswith('tools') or mod == 'config':
            del sys.modules[mod]

    from tools import discover_neighborhoods, search_google_places, search_web_restaurants, aggregate_restaurants
    tools['dining'] = [discover_neighborhoods, search_google_places, search_web_restaurants, aggregate_restaurants]

    # --- Events Agent ---
    sys.path = [p for p in original_path if 'weekender' not in p]
    sys.path.insert(0, os.path.join(_langchain_dir, "Events Agent"))
    for mod in list(sys.modules.keys()):
        if mod.startswith('tools') or mod == 'config':
            del sys.modules[mod]

    from tools import search_ticketmaster_events, search_web_events, aggregate_events
    tools['events'] = [search_ticketmaster_events, search_web_events, aggregate_events]

    # --- Locations Agent ---
    sys.path = [p for p in original_path if 'weekender' not in p]
    sys.path.insert(0, os.path.join(_langchain_dir, "Locations Agent"))
    for mod in list(sys.modules.keys()):
        if mod.startswith('tools') or mod == 'config':
            del sys.modules[mod]

    from tools import search_google_places_attractions, search_web_locations, aggregate_locations
    tools['locations'] = [search_google_places_attractions, search_web_locations, aggregate_locations]

    # Restore original path
    sys.path = original_path

    return tools


# Import all tools once at module load
_ALL_TOOLS = _import_all_tools()


# =============================================================================
# Agent Definitions
# =============================================================================

def get_model():
    """Get Claude model for agents."""
    return ChatAnthropic(
        model="claude-sonnet-4-20250514",
        anthropic_api_key=ANTHROPIC_API_KEY,
        temperature=0,
        max_tokens=8192  # Increased from 4096 to prevent truncation
    )


class ConcertAgent:
    """Agent for finding concerts."""

    name = "concerts"

    SYSTEM_PROMPT = """You are a concert discovery agent. Find concerts efficiently.

TOOLS:
1. search_ticketmaster(latitude: float, longitude: float, radius_miles: int, start_date: str, end_date: str)
   - All parameters REQUIRED
   - Returns: List of concert objects from Ticketmaster API

WORKFLOW:
1. Call search_ticketmaster with the provided coordinates and dates
2. Return the results directly as JSON

RULES:
- Be concise - don't repeat large data structures in responses
- Return the tool results directly as your final answer"""

    def __init__(self):
        self.tools = _ALL_TOOLS['concert']
        self.agent = create_react_agent(get_model(), self.tools)

    def run(self, city: str, lat: float, lon: float, start_date: str, end_date: str):
        """Run the concert agent."""
        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=f"""Find concerts in {city} from {start_date} to {end_date}.

Coordinates: {lat}, {lon}
Search radius: 25 miles

Execute the workflow and return aggregated results.""")
        ]

        result = self.agent.invoke(
            {"messages": messages},
            {"recursion_limit": 25}
        )
        return self._extract_results(result)

    def _extract_results(self, result):
        """Extract concert list from agent result."""
        import json
        for msg in reversed(result.get("messages", [])):
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                if '"venue"' in msg.content and '"source"' in msg.content:
                    try:
                        data = json.loads(msg.content)
                        if isinstance(data, list):
                            return data
                    except:
                        pass
        return []


class DiningAgent:
    """Agent for finding restaurants."""

    name = "dining"

    SYSTEM_PROMPT = """You are a restaurant discovery agent. Find great restaurants efficiently.

TOOLS:
1. discover_neighborhoods(city: str, max_neighborhoods: int = 5)
   - city REQUIRED
   - Returns: List of trendy neighborhood names

2. search_google_places(city: str, neighborhoods: list = [], cuisine_type: str = None)
   - city REQUIRED
   - Returns: List of restaurant objects from Google Places

3. search_web_restaurants(city: str, neighborhoods: list = [])
   - city REQUIRED
   - Returns: Raw page contents from Eater, Infatuation, Reddit

4. aggregate_restaurants(google_places_results: list, web_page_contents: list, city: str, neighborhoods: list = [])
   - google_places_results REQUIRED: Pass the list from search_google_places
   - web_page_contents REQUIRED: Pass the list from search_web_restaurants
   - city REQUIRED: City name string
   - Returns: Deduplicated, ranked restaurant list

WORKFLOW:
1. Call discover_neighborhoods for the city
2. Call search_google_places and search_web_restaurants (can be parallel)
3. Call aggregate_restaurants with ALL 3 required parameters
4. Return the aggregated results

RULES:
- Be concise - don't repeat large data structures in responses
- Always pass ALL required parameters to aggregate_restaurants
- If a tool fails, read the error and retry with correct parameters (max 2 retries)
- Never manually format results - always use the aggregation tool"""

    def __init__(self):
        self.tools = _ALL_TOOLS['dining']
        self.agent = create_react_agent(get_model(), self.tools)

    def run(self, city: str, lat: float, lon: float, start_date: str, end_date: str):
        """Run the dining agent."""
        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=f"""Find restaurants in {city}.

Coordinates: {lat}, {lon}

Execute the workflow and return aggregated results.""")
        ]

        result = self.agent.invoke(
            {"messages": messages},
            {"recursion_limit": 25}
        )
        return self._extract_results(result)

    def _extract_results(self, result):
        """Extract restaurant list from agent result."""
        import json
        for msg in reversed(result.get("messages", [])):
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                if '"name"' in msg.content and ('"rating"' in msg.content or '"neighborhood"' in msg.content):
                    try:
                        data = json.loads(msg.content)
                        if isinstance(data, list):
                            return data
                    except:
                        pass
        return []


class EventsAgent:
    """Agent for finding events."""

    name = "events"

    SYSTEM_PROMPT = """You are an events discovery agent. Find events (sports, theater, festivals) efficiently.

TOOLS:
1. search_ticketmaster_events(city: str, start_date: str, end_date: str, radius_miles: int = 25)
   - city, start_date, end_date REQUIRED
   - Returns: List of event objects from Ticketmaster (non-music)

2. search_web_events(city: str, start_date: str, end_date: str)
   - All 3 parameters REQUIRED
   - Returns: Raw page contents from Eventbrite, Timeout, etc.

3. aggregate_events(ticketmaster_results: list, web_page_contents: list, city: str, start_date: str, end_date: str)
   - ticketmaster_results REQUIRED: Pass the list from search_ticketmaster_events
   - web_page_contents REQUIRED: Pass the list from search_web_events
   - city REQUIRED: City name string
   - start_date REQUIRED: Start date string (YYYY-MM-DD)
   - end_date REQUIRED: End date string (YYYY-MM-DD)
   - Returns: Deduplicated, sorted event list

WORKFLOW:
1. Call search_ticketmaster_events and search_web_events in parallel
2. Call aggregate_events with ALL 5 required parameters
3. Return the aggregated results

RULES:
- Be concise - don't repeat large data structures in responses
- Always pass ALL required parameters to aggregate_events
- If a tool fails, read the error and retry with correct parameters (max 2 retries)
- Never manually format results - always use the aggregation tool"""

    def __init__(self):
        self.tools = _ALL_TOOLS['events']
        self.agent = create_react_agent(get_model(), self.tools)

    def run(self, city: str, lat: float, lon: float, start_date: str, end_date: str):
        """Run the events agent."""
        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=f"""Find events in {city} from {start_date} to {end_date}.

Coordinates: {lat}, {lon}
Search radius: 20 miles

Execute the workflow and return aggregated results.""")
        ]

        result = self.agent.invoke(
            {"messages": messages},
            {"recursion_limit": 25}
        )
        return self._extract_results(result)

    def _extract_results(self, result):
        """Extract events list from agent result."""
        import json
        for msg in reversed(result.get("messages", [])):
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                if '"name"' in msg.content and '"category"' in msg.content:
                    try:
                        data = json.loads(msg.content)
                        if isinstance(data, list):
                            return data
                    except:
                        pass
        return []


class LocationsAgent:
    """Agent for finding attractions and locations."""

    name = "locations"

    SYSTEM_PROMPT = """You are a locations discovery agent. Find attractions and hidden gems efficiently.

TOOLS:
1. search_google_places_attractions(city: str, attraction_types: list = [])
   - city REQUIRED
   - Returns: List of attraction objects from Google Places

2. search_web_locations(city: str)
   - city REQUIRED
   - Returns: Raw page contents from Reddit, Atlas Obscura, Timeout

3. aggregate_locations(google_places_results: list, web_page_contents: list, city: str)
   - google_places_results REQUIRED: Pass the list from search_google_places_attractions
   - web_page_contents REQUIRED: Pass the list from search_web_locations
   - city REQUIRED: City name string
   - Returns: Deduplicated, categorized location list

WORKFLOW:
1. Call search_google_places_attractions and search_web_locations in parallel
2. Call aggregate_locations with ALL 3 required parameters
3. Return the aggregated results

RULES:
- Be concise - don't repeat large data structures in responses
- Always pass ALL required parameters to aggregate_locations
- If a tool fails, read the error and retry with correct parameters (max 2 retries)
- Never manually format results - always use the aggregation tool"""

    def __init__(self):
        self.tools = _ALL_TOOLS['locations']
        self.agent = create_react_agent(get_model(), self.tools)

    def run(self, city: str, lat: float, lon: float, start_date: str, end_date: str):
        """Run the locations agent."""
        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=f"""Find attractions and locations in {city}.

Coordinates: {lat}, {lon}

Execute the workflow and return aggregated results.""")
        ]

        result = self.agent.invoke(
            {"messages": messages},
            {"recursion_limit": 25}
        )
        return self._extract_results(result)

    def _extract_results(self, result):
        """Extract locations list from agent result."""
        import json
        for msg in reversed(result.get("messages", [])):
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                if '"name"' in msg.content and ('"category"' in msg.content or '"source"' in msg.content):
                    try:
                        data = json.loads(msg.content)
                        if isinstance(data, list):
                            return data
                    except:
                        pass
        return []
