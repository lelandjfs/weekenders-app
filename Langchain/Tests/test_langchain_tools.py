"""
Simple LangChain Tools Test
Shows how to wrap our working APIs as LangChain tools
No LLM/OpenAI needed - just testing the tool wrapper pattern
"""

import requests
import json
from langchain_core.tools import tool

# API Keys
TICKETMASTER_KEY = "wtwlR1qylRp6pwQwTbMHmAFqQG8B1zRl"
GOOGLE_PLACES_KEY = "AIzaSyDlm4Xvd-t4MCck_HukfI1MlEIgdJQ3MfA"
TAVILY_KEY = "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"


# ============================================================
# Wrap APIs as LangChain Tools
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

            return json.dumps({"concerts": formatted_events, "count": len(formatted_events)}, indent=2)
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

            return json.dumps({"restaurants": formatted_restaurants, "count": len(formatted_restaurants)}, indent=2)
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

            return json.dumps({"results": formatted_results, "count": len(formatted_results)}, indent=2)
        else:
            return json.dumps({"results": [], "count": 0, "message": "No results found"})

    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================
# Test the LangChain Tools
# ============================================================

def test_langchain_tools():
    """Test each LangChain tool"""
    print("\n" + "="*60)
    print("TESTING LANGCHAIN TOOLS")
    print("="*60)
    print("\nThese are now LangChain @tool decorated functions")
    print("They can be used by LangChain agents or called directly\n")

    # Test 1: Concerts
    print("="*60)
    print("1. Testing get_concerts tool")
    print("="*60)
    concerts_result = get_concerts.invoke({"city": "Austin", "country_code": "US"})
    concerts_data = json.loads(concerts_result)
    print(f"\nFound {concerts_data.get('count', 0)} concerts:")
    if concerts_data.get('concerts'):
        for concert in concerts_data['concerts'][:2]:  # Show first 2
            print(f"  • {concert['name']} at {concert['venue']} on {concert['date']}")

    # Test 2: Restaurants
    print("\n" + "="*60)
    print("2. Testing get_restaurants tool")
    print("="*60)
    restaurants_result = get_restaurants.invoke({"city": "Austin", "state": "Texas"})
    restaurants_data = json.loads(restaurants_result)
    print(f"\nFound {restaurants_data.get('count', 0)} restaurants:")
    if restaurants_data.get('restaurants'):
        for restaurant in restaurants_data['restaurants'][:2]:  # Show first 2
            print(f"  • {restaurant['name']} (Rating: {restaurant['rating']})")

    # Test 3: Web Search
    print("\n" + "="*60)
    print("3. Testing search_web tool")
    print("="*60)
    search_result = search_web.invoke({"query": "best things to do in Austin Texas"})
    search_data = json.loads(search_result)
    print(f"\nFound {search_data.get('count', 0)} web results:")
    if search_data.get('results'):
        for result in search_data['results'][:2]:  # Show first 2
            print(f"  • {result['title']}")
            print(f"    {result['url']}")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("\n✅ All LangChain tools working!")
    print("\nThese tools are now ready to be used by:")
    print("  1. LangChain agents (with an LLM like GPT-4)")
    print("  2. LangGraph workflows (deterministic orchestration)")
    print("  3. Direct function calls (like we just did)")
    print("\nNext step: Build a simple agent or LangGraph workflow")


if __name__ == "__main__":
    test_langchain_tools()
