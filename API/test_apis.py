"""
Simple API Tests for Weekenders App
Test each API individually before integrating with LangChain
"""

import requests
import json
from datetime import datetime, timedelta

# API Keys
import os
from dotenv import load_dotenv
load_dotenv()

TICKETMASTER_KEY = os.getenv("TICKETMASTER_API_KEY")
GOOGLE_PLACES_KEY = os.getenv("GOOGLE_PLACES_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")


def test_ticketmaster():
    """Test Ticketmaster API - Get concerts in Austin"""
    print("\n" + "="*60)
    print("TESTING TICKETMASTER API")
    print("="*60)

    url = "https://app.ticketmaster.com/discovery/v2/events.json"

    # Get events in Austin for next week
    params = {
        "apikey": TICKETMASTER_KEY,
        "city": "Austin",
        "countryCode": "US",
        "classificationName": "music",  # Focus on concerts
        "size": 5  # Limit to 5 results for testing
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        # Check if we got events
        if "_embedded" in data and "events" in data["_embedded"]:
            events = data["_embedded"]["events"]
            print(f"\n✅ SUCCESS! Found {len(events)} events in Austin")

            # Print first event details
            if events:
                event = events[0]
                print(f"\nSample Event:")
                print(f"  Name: {event.get('name', 'N/A')}")
                print(f"  Date: {event.get('dates', {}).get('start', {}).get('localDate', 'N/A')}")
                print(f"  Venue: {event.get('_embedded', {}).get('venues', [{}])[0].get('name', 'N/A')}")
                print(f"  URL: {event.get('url', 'N/A')}")
        else:
            print(f"\n⚠️  No events found in response")

        print(f"\nFull response structure: {list(data.keys())}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERROR: {e}")
        return False


def test_google_places():
    """Test Google Places API - Get restaurants in Austin"""
    print("\n" + "="*60)
    print("TESTING GOOGLE PLACES API")
    print("="*60)

    # Using the new Places API (New) - Text Search endpoint
    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.priceLevel"
    }

    # Search for restaurants in Austin
    body = {
        "textQuery": "restaurants in Austin, Texas",
        "maxResultCount": 5
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()

        data = response.json()

        # Check if we got places
        if "places" in data:
            places = data["places"]
            print(f"\n✅ SUCCESS! Found {len(places)} restaurants in Austin")

            # Print first restaurant details
            if places:
                place = places[0]
                print(f"\nSample Restaurant:")
                print(f"  Name: {place.get('displayName', {}).get('text', 'N/A')}")
                print(f"  Address: {place.get('formattedAddress', 'N/A')}")
                print(f"  Rating: {place.get('rating', 'N/A')}")
                print(f"  Price: {place.get('priceLevel', 'N/A')}")
        else:
            print(f"\n⚠️  No places found in response")

        print(f"\nFull response structure: {list(data.keys())}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERROR: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False


def test_tavily():
    """Test Tavily API - Search for Austin events"""
    print("\n" + "="*60)
    print("TESTING TAVILY API")
    print("="*60)

    url = "https://api.tavily.com/search"

    headers = {
        "Content-Type": "application/json"
    }

    body = {
        "api_key": TAVILY_KEY,
        "query": "best restaurants in Austin Texas",
        "max_results": 5
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()

        data = response.json()

        # Check if we got results
        if "results" in data:
            results = data["results"]
            print(f"\n✅ SUCCESS! Found {len(results)} search results")

            # Print first result
            if results:
                result = results[0]
                print(f"\nSample Search Result:")
                print(f"  Title: {result.get('title', 'N/A')}")
                print(f"  URL: {result.get('url', 'N/A')}")
                print(f"  Content: {result.get('content', 'N/A')[:150]}...")
        else:
            print(f"\n⚠️  No results found in response")

        print(f"\nFull response structure: {list(data.keys())}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERROR: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False


def run_all_tests():
    """Run all API tests"""
    print("\n" + "🚀 " + "="*56)
    print("WEEKENDERS APP - API CONNECTIVITY TEST")
    print("="*58)
    print("\nTesting location: Austin, Texas")
    print("Testing 3 APIs: Ticketmaster, Google Places, Tavily")

    results = {
        "Ticketmaster": test_ticketmaster(),
        "Google Places": test_google_places(),
        "Tavily": test_tavily()
    }

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for api, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{api:20} {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 All APIs working! Ready to integrate with LangChain.")
    else:
        print("\n⚠️  Some APIs failed. Check errors above.")

    return all_passed


if __name__ == "__main__":
    run_all_tests()
