"""
Weekender Parallel Runner
==========================

Runs data fetching in parallel with Redis caching, then passes to agents for aggregation.
"""

import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langsmith import traceable
from config import setup_langsmith, get_local_ticketmaster_dates
from cache import get_cached, set_cached

# Initialize LangSmith tracing at module load (before any @traceable functions run)
setup_langsmith()

# =============================================================================
# City Coordinates
# =============================================================================

CITY_COORDS = {
    "austin": (30.2672, -97.7431),
    "new york": (40.7128, -74.0060),
    "los angeles": (34.0522, -118.2437),
    "chicago": (41.8781, -87.6298),
    "san francisco": (37.7749, -122.4194),
    "denver": (39.7392, -104.9903),
    "nashville": (36.1627, -86.7816),
    "seattle": (47.6062, -122.3321),
    "portland": (45.5155, -122.6789),
    "miami": (25.7617, -80.1918),
    "new orleans": (29.9511, -90.0715),
    "boston": (42.3601, -71.0589),
    "atlanta": (33.7490, -84.3880),
    "philadelphia": (39.9526, -75.1652),
    "dallas": (32.7767, -96.7970),
    "houston": (29.7604, -95.3698),
    "phoenix": (33.4484, -112.0740),
    "san diego": (32.7157, -117.1611),
    "minneapolis": (44.9778, -93.2650),
    "detroit": (42.3314, -83.0458),
}


def get_coordinates(city: str) -> tuple:
    """Get lat/lon for a city."""
    city_lower = city.lower().strip()
    if city_lower in CITY_COORDS:
        return CITY_COORDS[city_lower]
    print(f"  Note: Using default coordinates for unknown city '{city}'")
    return (30.2672, -97.7431)


def get_weekend_dates(weekend: str = "this") -> tuple:
    """Get start and end dates for weekend.

    Args:
        weekend: "this", "next", or "two-weeks"
    """
    today = datetime.now()
    days_until_thursday = (3 - today.weekday()) % 7

    # If it's already past Thursday noon, default to next week
    if days_until_thursday == 0 and today.hour >= 12:
        days_until_thursday = 7

    if weekend == "next":
        days_until_thursday += 7
    elif weekend == "two-weeks":
        days_until_thursday += 14

    thursday = today + timedelta(days=days_until_thursday)
    saturday = thursday + timedelta(days=2)
    return thursday.strftime("%Y-%m-%d"), saturday.strftime("%Y-%m-%d")


# =============================================================================
# Import Tools (done at module level to avoid repeated imports)
# =============================================================================

def _import_tools():
    """Import all tools from Langchain agents."""
    tools = {}
    langchain_dir = os.path.join(os.path.dirname(__file__), "..", "Langchain")
    original_path = sys.path.copy()

    # Concert tools
    sys.path = [p for p in original_path if 'weekender' not in p]
    sys.path.insert(0, os.path.join(langchain_dir, "Concert Agent"))
    for mod in list(sys.modules.keys()):
        if mod.startswith('tools') or mod == 'config':
            del sys.modules[mod]
    from tools import search_ticketmaster
    tools['search_ticketmaster'] = search_ticketmaster

    # Dining tools
    sys.path = [p for p in original_path if 'weekender' not in p]
    sys.path.insert(0, os.path.join(langchain_dir, "Dining Agent"))
    for mod in list(sys.modules.keys()):
        if mod.startswith('tools') or mod == 'config':
            del sys.modules[mod]
    from tools import discover_neighborhoods, search_google_places, search_web_restaurants, aggregate_restaurants
    tools['discover_neighborhoods'] = discover_neighborhoods
    tools['search_google_places'] = search_google_places
    tools['search_web_restaurants'] = search_web_restaurants
    tools['aggregate_restaurants'] = aggregate_restaurants

    # Events tools
    sys.path = [p for p in original_path if 'weekender' not in p]
    sys.path.insert(0, os.path.join(langchain_dir, "Events Agent"))
    for mod in list(sys.modules.keys()):
        if mod.startswith('tools') or mod == 'config':
            del sys.modules[mod]
    from tools import search_ticketmaster_events, search_web_events, aggregate_events
    tools['search_ticketmaster_events'] = search_ticketmaster_events
    tools['search_web_events'] = search_web_events
    tools['aggregate_events'] = aggregate_events

    # Locations tools
    sys.path = [p for p in original_path if 'weekender' not in p]
    sys.path.insert(0, os.path.join(langchain_dir, "Locations Agent"))
    for mod in list(sys.modules.keys()):
        if mod.startswith('tools') or mod == 'config':
            del sys.modules[mod]
    from tools import search_google_places_attractions, search_web_locations, aggregate_locations
    tools['search_google_places_attractions'] = search_google_places_attractions
    tools['search_web_locations'] = search_web_locations
    tools['aggregate_locations'] = aggregate_locations

    sys.path = original_path
    return tools


TOOLS = _import_tools()


# =============================================================================
# Fetch Functions (with caching)
# =============================================================================

@traceable(name="fetch_concerts", run_type="tool", metadata={"category": "concerts"})
def fetch_concerts(city: str, lat: float, lon: float, start_date: str, end_date: str) -> list:
    """Fetch concerts from Ticketmaster."""
    cache_key = "concerts"
    cached = get_cached(cache_key, city, start_date, end_date)
    if cached is not None:
        return cached

    print(f"   [Concerts] Fetching from Ticketmaster...")
    try:
        utc_start, utc_end = get_local_ticketmaster_dates(lat, lon, start_date, end_date)
        results = TOOLS['search_ticketmaster'].invoke({
            "latitude": lat,
            "longitude": lon,
            "radius_miles": 25,
            "start_date": utc_start,
            "end_date": utc_end
        })
        set_cached(cache_key, city, results, start_date, end_date)
        return results
    except Exception as e:
        print(f"   [Concerts] Error: {e}")
        return []


@traceable(name="fetch_events_ticketmaster", run_type="tool", metadata={"category": "events"})
def fetch_events_ticketmaster(city: str, lat: float, lon: float, start_date: str, end_date: str) -> list:
    """Fetch events from Ticketmaster."""
    cache_key = "events_tm"
    cached = get_cached(cache_key, city, start_date, end_date)
    if cached is not None:
        return cached

    print(f"   [Events] Fetching from Ticketmaster...")
    try:
        utc_start, utc_end = get_local_ticketmaster_dates(lat, lon, start_date, end_date)
        results = TOOLS['search_ticketmaster_events'].invoke({
            "city": city,
            "start_date": utc_start,
            "end_date": utc_end,
            "radius_miles": 20
        })
        set_cached(cache_key, city, results, start_date, end_date)
        return results
    except Exception as e:
        print(f"   [Events] Ticketmaster error: {e}")
        return []


@traceable(name="fetch_events_web", run_type="tool", metadata={"category": "events"})
def fetch_events_web(city: str, start_date: str, end_date: str) -> list:
    """Fetch events from web sources."""
    cache_key = "events_web"
    cached = get_cached(cache_key, city, start_date, end_date)
    if cached is not None:
        return cached

    print(f"   [Events] Fetching from web sources...")
    try:
        results = TOOLS['search_web_events'].invoke({
            "city": city,
            "start_date": start_date,
            "end_date": end_date
        })
        set_cached(cache_key, city, results, start_date, end_date)
        return results
    except Exception as e:
        print(f"   [Events] Web error: {e}")
        return []


@traceable(name="fetch_neighborhoods", run_type="tool", metadata={"category": "dining"})
def fetch_neighborhoods(city: str) -> list:
    """Fetch neighborhoods."""
    cache_key = "neighborhoods"
    cached = get_cached(cache_key, city)
    if cached is not None:
        return cached

    print(f"   [Dining] Discovering neighborhoods...")
    try:
        results = TOOLS['discover_neighborhoods'].invoke({
            "city": city,
            "max_neighborhoods": 5
        })
        set_cached(cache_key, city, results)
        return results
    except Exception as e:
        print(f"   [Dining] Neighborhoods error: {e}")
        return []


@traceable(name="fetch_restaurants_google", run_type="tool", metadata={"category": "dining"})
def fetch_restaurants_google(city: str, neighborhoods: list) -> list:
    """Fetch restaurants from Google Places."""
    cache_key = "restaurants_google"
    cached = get_cached(cache_key, city)
    if cached is not None:
        return cached

    print(f"   [Dining] Fetching from Google Places...")
    try:
        results = TOOLS['search_google_places'].invoke({
            "city": city,
            "neighborhoods": neighborhoods or []
        })
        set_cached(cache_key, city, results)
        return results
    except Exception as e:
        print(f"   [Dining] Google Places error: {e}")
        return []


@traceable(name="fetch_restaurants_web", run_type="tool", metadata={"category": "dining"})
def fetch_restaurants_web(city: str, neighborhoods: list) -> list:
    """Fetch restaurants from web sources."""
    cache_key = "restaurants_web"
    cached = get_cached(cache_key, city)
    if cached is not None:
        return cached

    print(f"   [Dining] Fetching from web sources...")
    try:
        results = TOOLS['search_web_restaurants'].invoke({
            "city": city,
            "neighborhoods": neighborhoods or []
        })
        set_cached(cache_key, city, results)
        return results
    except Exception as e:
        print(f"   [Dining] Web error: {e}")
        return []


@traceable(name="fetch_locations_google", run_type="tool", metadata={"category": "locations"})
def fetch_locations_google(city: str) -> list:
    """Fetch locations from Google Places."""
    cache_key = "locations_google"
    cached = get_cached(cache_key, city)
    if cached is not None:
        return cached

    print(f"   [Locations] Fetching from Google Places...")
    try:
        results = TOOLS['search_google_places_attractions'].invoke({
            "city": city
        })
        set_cached(cache_key, city, results)
        return results
    except Exception as e:
        print(f"   [Locations] Google Places error: {e}")
        return []


@traceable(name="fetch_locations_web", run_type="tool", metadata={"category": "locations"})
def fetch_locations_web(city: str) -> list:
    """Fetch locations from web sources."""
    cache_key = "locations_web"
    cached = get_cached(cache_key, city)
    if cached is not None:
        return cached

    print(f"   [Locations] Fetching from web sources...")
    try:
        results = TOOLS['search_web_locations'].invoke({
            "city": city
        })
        set_cached(cache_key, city, results)
        return results
    except Exception as e:
        print(f"   [Locations] Web error: {e}")
        return []


# =============================================================================
# Aggregation Functions
# =============================================================================

@traceable(name="aggregate_events", run_type="chain", metadata={"category": "events"})
def aggregate_events_data(tm_results: list, web_results: list, city: str, start_date: str, end_date: str) -> list:
    """Aggregate events using the tool."""
    if not tm_results and not web_results:
        return []

    print(f"   [Events] Aggregating {len(tm_results)} TM + {len(web_results)} web results...")
    try:
        results = TOOLS['aggregate_events'].invoke({
            "ticketmaster_results": tm_results or [],
            "web_page_contents": web_results or [],
            "city": city,
            "start_date": start_date,
            "end_date": end_date
        })
        return results
    except Exception as e:
        print(f"   [Events] Aggregation error: {e}")
        return tm_results or []


@traceable(name="aggregate_dining", run_type="chain", metadata={"category": "dining"})
def aggregate_restaurants_data(google_results: list, web_results: list, city: str, neighborhoods: list) -> list:
    """Aggregate restaurants using the tool."""
    if not google_results and not web_results:
        return []

    print(f"   [Dining] Aggregating {len(google_results)} Google + {len(web_results)} web results...")
    try:
        results = TOOLS['aggregate_restaurants'].invoke({
            "google_places_results": google_results or [],
            "web_page_contents": web_results or [],
            "city": city,
            "neighborhoods": neighborhoods or []
        })
        return results
    except Exception as e:
        print(f"   [Dining] Aggregation error: {e}")
        return google_results or []


@traceable(name="aggregate_locations", run_type="chain", metadata={"category": "locations"})
def aggregate_locations_data(google_results: list, web_results: list, city: str) -> list:
    """Aggregate locations using the tool."""
    if not google_results and not web_results:
        return []

    print(f"   [Locations] Aggregating {len(google_results)} Google + {len(web_results)} web results...")
    try:
        results = TOOLS['aggregate_locations'].invoke({
            "google_places_results": google_results or [],
            "web_page_contents": web_results or [],
            "city": city
        })
        return results
    except Exception as e:
        print(f"   [Locations] Aggregation error: {e}")
        return google_results or []


# =============================================================================
# Main Runner
# =============================================================================

@traceable(name="weekender_pipeline", run_type="chain")
def run_all_agents(city: str, weekend: str = "next") -> dict:
    """Run all data fetching in parallel, then aggregate."""
    lat, lon = get_coordinates(city)
    start_date, end_date = get_weekend_dates(weekend)

    results = {
        "city": city,
        "coordinates": (lat, lon),
        "start_date": start_date,
        "end_date": end_date,
        "concerts": [],
        "dining": [],
        "events": [],
        "locations": [],
        "errors": []
    }

    # Phase 1: Parallel data fetching
    print("\n   Phase 1: Fetching data in parallel...")

    fetch_results = {}

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            # Concerts
            executor.submit(fetch_concerts, city, lat, lon, start_date, end_date): "concerts",

            # Events
            executor.submit(fetch_events_ticketmaster, city, lat, lon, start_date, end_date): "events_tm",
            executor.submit(fetch_events_web, city, start_date, end_date): "events_web",

            # Dining (neighborhoods first, then parallel)
            executor.submit(fetch_neighborhoods, city): "neighborhoods",

            # Locations
            executor.submit(fetch_locations_google, city): "locations_google",
            executor.submit(fetch_locations_web, city): "locations_web",
        }

        for future in as_completed(futures):
            name = futures[future]
            try:
                fetch_results[name] = future.result()
            except Exception as e:
                print(f"   Error in {name}: {e}")
                fetch_results[name] = []
                results["errors"].append({"source": name, "error": str(e)})

    # Fetch restaurants after neighborhoods (needs neighborhoods as input)
    neighborhoods = fetch_results.get("neighborhoods", [])

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(fetch_restaurants_google, city, neighborhoods): "restaurants_google",
            executor.submit(fetch_restaurants_web, city, neighborhoods): "restaurants_web",
        }

        for future in as_completed(futures):
            name = futures[future]
            try:
                fetch_results[name] = future.result()
            except Exception as e:
                print(f"   Error in {name}: {e}")
                fetch_results[name] = []

    # Phase 2: Aggregation
    print("\n   Phase 2: Aggregating results...")

    # Concerts (no aggregation needed - already clean from Ticketmaster)
    results["concerts"] = fetch_results.get("concerts", [])

    # Events aggregation
    try:
        results["events"] = aggregate_events_data(
            fetch_results.get("events_tm", []),
            fetch_results.get("events_web", []),
            city, start_date, end_date
        )
    except Exception as e:
        results["errors"].append({"agent": "events", "error": str(e)})
        results["events"] = fetch_results.get("events_tm", [])

    # Dining aggregation
    try:
        results["dining"] = aggregate_restaurants_data(
            fetch_results.get("restaurants_google", []),
            fetch_results.get("restaurants_web", []),
            city, neighborhoods
        )
    except Exception as e:
        results["errors"].append({"agent": "dining", "error": str(e)})
        results["dining"] = fetch_results.get("restaurants_google", [])

    # Locations aggregation
    try:
        results["locations"] = aggregate_locations_data(
            fetch_results.get("locations_google", []),
            fetch_results.get("locations_web", []),
            city
        )
    except Exception as e:
        results["errors"].append({"agent": "locations", "error": str(e)})
        results["locations"] = fetch_results.get("locations_google", [])

    return results


# =============================================================================
# Main (for testing)
# =============================================================================

if __name__ == "__main__":
    city = input("City: ").strip() or "Austin"
    weekend = input("Weekend (this/next) [next]: ").strip() or "next"

    print(f"\nRunning for {city}...")
    results = run_all_agents(city, weekend)

    print(f"\nResults:")
    print(f"  Concerts: {len(results['concerts'])}")
    print(f"  Dining: {len(results['dining'])}")
    print(f"  Events: {len(results['events'])}")
    print(f"  Locations: {len(results['locations'])}")

    if results['errors']:
        print(f"\nErrors: {results['errors']}")
