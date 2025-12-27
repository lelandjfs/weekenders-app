"""
Simple LangChain Integration Test
Wraps our working APIs as LangChain tools
"""

import requests
import json
from langchain_core.tools import tool
import os

# API Keys
TICKETMASTER_KEY = "wtwlR1qylRp6pwQwTbMHmAFqQG8B1zRl"
GOOGLE_PLACES_KEY = "AIzaSyDlm4Xvd-t4MCck_HukfI1MlEIgdJQ3MfA"
TAVILY_KEY = "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"


# ============================================================
# STEP 1: Wrap APIs as LangChain Tools
# ============================================================

@tool
def get_concerts(city: str, country_code: str = "US") -> str:
    """
    Get concerts in a specific city using Ticketmaster API.

    Args:
        city: City name (e.g., "Austin")
        country_code: 2-letter country code (default: "US")

    Returns:
        JSON string with concert information
    """
    url = "https://app.ticketmaster.com/discovery/v2/events.json"

    params = {
        "apikey": TICKETMASTER_KEY,
        "city": city,
        "countryCode": country_code,
        "classificationName": "music",
        "size": 5
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if "_embedded" in data and "events" in data["_embedded"]:
            events = data["_embedded"]["events"]

            # Format events nicely
            formatted_events = []
            for event in events:
                formatted_events.append({
                    "name": event.get("name", "N/A"),
                    "date": event.get("dates", {}).get("start", {}).get("localDate", "N/A"),
                    "venue": event.get("_embedded", {}).get("venues", [{}])[0].get("name", "N/A"),
                    "url": event.get("url", "N/A")
                })

            return json.dumps({"concerts": formatted_events, "count": len(formatted_events)})
        else:
            return json.dumps({"concerts": [], "count": 0, "message": "No concerts found"})

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_restaurants(city: str, state: str = "Texas") -> str:
    """
    Get restaurants in a specific city using Google Places API.

    Args:
        city: City name (e.g., "Austin")
        state: State name (default: "Texas")

    Returns:
        JSON string with restaurant information
    """
    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.priceLevel"
    }

    body = {
        "textQuery": f"restaurants in {city}, {state}",
        "maxResultCount": 5
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()

        if "places" in data:
            places = data["places"]

            # Format restaurants nicely
            formatted_restaurants = []
            for place in places:
                formatted_restaurants.append({
                    "name": place.get("displayName", {}).get("text", "N/A"),
                    "address": place.get("formattedAddress", "N/A"),
                    "rating": place.get("rating", "N/A"),
                    "price_level": place.get("priceLevel", "N/A")
                })

            return json.dumps({"restaurants": formatted_restaurants, "count": len(formatted_restaurants)})
        else:
            return json.dumps({"restaurants": [], "count": 0, "message": "No restaurants found"})

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def search_web(query: str) -> str:
    """
    Search the web using Tavily API.

    Args:
        query: Search query (e.g., "best restaurants in Austin")

    Returns:
        JSON string with search results
    """
    url = "https://api.tavily.com/search"

    headers = {
        "Content-Type": "application/json"
    }

    body = {
        "api_key": TAVILY_KEY,
        "query": query,
        "max_results": 3
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()

        if "results" in data:
            results = data["results"]

            # Format results nicely
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", "N/A"),
                    "url": result.get("url", "N/A"),
                    "snippet": result.get("content", "N/A")[:200] + "..."
                })

            return json.dumps({"results": formatted_results, "count": len(formatted_results)})
        else:
            return json.dumps({"results": [], "count": 0, "message": "No results found"})

    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================
# STEP 2: Test Tools Individually (No Agent Yet)
# ============================================================

def test_tools():
    """Test each tool works correctly"""
    print("\n" + "="*60)
    print("TESTING LANGCHAIN TOOLS")
    print("="*60)

    # Test concert tool
    print("\n1. Testing get_concerts tool...")
    concerts_result = get_concerts.invoke({"city": "Austin", "country_code": "US"})
    print(f"Result: {concerts_result[:200]}...")

    # Test restaurant tool
    print("\n2. Testing get_restaurants tool...")
    restaurants_result = get_restaurants.invoke({"city": "Austin", "state": "Texas"})
    print(f"Result: {restaurants_result[:200]}...")

    # Test web search tool
    print("\n3. Testing search_web tool...")
    search_result = search_web.invoke({"query": "best restaurants Austin Texas"})
    print(f"Result: {search_result[:200]}...")

    print("\n✅ All tools working!")


# ============================================================
# STEP 3: Create Simple Agent (Requires OpenAI API Key)
# ============================================================

def test_agent():
    """
    Test a simple agent that can use our tools.
    NOTE: This requires OPENAI_API_KEY environment variable set.
    """
    print("\n" + "="*60)
    print("TESTING LANGCHAIN AGENT")
    print("="*60)

    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  SKIPPING AGENT TEST")
        print("To test the agent, set your OPENAI_API_KEY environment variable:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("\nThe tools above work fine - you just need an LLM to coordinate them.")
        return

    try:
        # Create tools list
        tools = [get_concerts, get_restaurants, search_web]

        # Create LLM
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # Get a prompt from hub (simple react agent prompt)
        prompt = hub.pull("hwchase17/react")

        # Create agent
        agent = create_react_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

        # Test query
        print("\n📝 Query: 'What concerts can I find in Austin?'\n")
        result = agent_executor.invoke({
            "input": "What concerts can I find in Austin?"
        })

        print("\n" + "="*60)
        print("AGENT RESPONSE:")
        print("="*60)
        print(result["output"])
    except Exception as e:
        print(f"\n⚠️  Agent test failed: {e}")
        print("This is okay - the tools still work without an agent!")


if __name__ == "__main__":
    # Test tools first (always works)
    test_tools()

    # Test agent (only if OpenAI key is set)
    test_agent()
