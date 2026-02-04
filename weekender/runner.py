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
    # California
    "san francisco": (37.7749, -122.4194),
    "los angeles": (34.0522, -118.2437),
    "san diego": (32.7157, -117.1611),
    "sacramento": (38.5816, -121.4944),
    "san jose": (37.3382, -121.8863),
    "oakland": (37.8044, -122.2712),
    "long beach": (33.7701, -118.1937),
    "santa monica": (34.0195, -118.4912),
    "berkeley": (37.8716, -122.2727),
    "pasadena": (34.1478, -118.1445),
    "fresno": (36.7378, -119.7871),
    "irvine": (33.6846, -117.8265),
    "santa barbara": (34.4208, -119.6982),
    # Texas
    "austin": (30.2672, -97.7431),
    "houston": (29.7604, -95.3698),
    "dallas": (32.7767, -96.7970),
    "san antonio": (29.4241, -98.4936),
    "fort worth": (32.7555, -97.3308),
    "el paso": (31.7619, -106.4850),
    # Northeast
    "new york": (40.7128, -74.0060),
    "brooklyn": (40.6782, -73.9442),
    "queens": (40.7282, -73.7949),
    "boston": (42.3601, -71.0589),
    "cambridge": (42.3736, -71.1097),
    "philadelphia": (39.9526, -75.1652),
    "pittsburgh": (40.4406, -79.9959),
    "baltimore": (39.2904, -76.6122),
    "washington": (38.9072, -77.0369),
    "providence": (41.8240, -71.4128),
    "buffalo": (42.8864, -78.8784),
    "rochester": (43.1566, -77.6088),
    "newark": (40.7357, -74.1724),
    "jersey city": (40.7178, -74.0431),
    "new haven": (41.3083, -72.9279),
    "hartford": (41.7658, -72.6734),
    "portland me": (43.6591, -70.2568),
    "burlington": (44.4759, -73.2121),
    # Southeast
    "miami": (25.7617, -80.1918),
    "atlanta": (33.7490, -84.3880),
    "nashville": (36.1627, -86.7816),
    "new orleans": (29.9511, -90.0715),
    "charlotte": (35.2271, -80.8431),
    "raleigh": (35.7796, -78.6382),
    "tampa": (27.9506, -82.4572),
    "orlando": (28.5383, -81.3792),
    "jacksonville": (30.3322, -81.6557),
    "savannah": (32.0809, -81.0912),
    "charleston": (32.7765, -79.9311),
    "richmond": (37.5407, -77.4360),
    "memphis": (35.1495, -90.0490),
    # Midwest
    "chicago": (41.8781, -87.6298),
    "detroit": (42.3314, -83.0458),
    "ann arbor": (42.2808, -83.7430),
    "minneapolis": (44.9778, -93.2650),
    "st. paul": (44.9537, -93.0900),
    "cleveland": (41.4993, -81.6944),
    "columbus": (39.9612, -82.9988),
    "cincinnati": (39.1031, -84.5120),
    "indianapolis": (39.7684, -86.1581),
    "milwaukee": (43.0389, -87.9065),
    "madison": (43.0731, -89.4012),
    "kansas city": (39.0997, -94.5786),
    "st. louis": (38.6270, -90.1994),
    # Mountain/West
    "denver": (39.7392, -104.9903),
    "boulder": (40.0150, -105.2705),
    "phoenix": (33.4484, -112.0740),
    "tucson": (32.2226, -110.9747),
    "las vegas": (36.1699, -115.1398),
    "reno": (39.5296, -119.8138),
    "salt lake city": (40.7608, -111.8910),
    "albuquerque": (35.0844, -106.6504),
    "santa fe": (35.6870, -105.9378),
    # Pacific Northwest
    "seattle": (47.6062, -122.3321),
    "portland": (45.5155, -122.6789),
    "tacoma": (47.2529, -122.4443),
    "spokane": (47.6588, -117.4260),
    "eugene": (44.0521, -123.0868),
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

def _is_rate_limit(error: Exception) -> bool:
    """Check if error is a rate limit."""
    err_str = str(error).lower()
    return any(x in err_str for x in ['429', 'rate limit', 'too many requests', 'quota'])


@traceable(name="fetch_concerts", run_type="tool", metadata={"category": "concerts"})
def fetch_concerts(city: str, lat: float, lon: float, start_date: str, end_date: str) -> dict:
    """Fetch concerts from Ticketmaster. Returns dict with data and error info."""
    cache_key = "concerts"
    cached = get_cached(cache_key, city, start_date, end_date)
    if cached is not None:
        return {"data": cached, "error": None, "source": "Ticketmaster"}

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
        return {"data": results, "error": None, "source": "Ticketmaster"}
    except Exception as e:
        print(f"   [Concerts] Error: {e}")
        error_type = "rate_limit" if _is_rate_limit(e) else "error"
        return {"data": [], "error": {"type": error_type, "message": str(e)}, "source": "Ticketmaster"}


@traceable(name="fetch_events_ticketmaster", run_type="tool", metadata={"category": "events"})
def fetch_events_ticketmaster(city: str, lat: float, lon: float, start_date: str, end_date: str) -> dict:
    """Fetch events from Ticketmaster."""
    cache_key = "events_tm"
    cached = get_cached(cache_key, city, start_date, end_date)
    if cached is not None:
        return {"data": cached, "error": None, "source": "Ticketmaster"}

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
        return {"data": results, "error": None, "source": "Ticketmaster"}
    except Exception as e:
        print(f"   [Events] Ticketmaster error: {e}")
        error_type = "rate_limit" if _is_rate_limit(e) else "error"
        return {"data": [], "error": {"type": error_type, "message": str(e)}, "source": "Ticketmaster"}


@traceable(name="fetch_events_web", run_type="tool", metadata={"category": "events"})
def fetch_events_web(city: str, start_date: str, end_date: str) -> dict:
    """Fetch events from web sources (Tavily)."""
    cache_key = "events_web"
    cached = get_cached(cache_key, city, start_date, end_date)
    if cached is not None:
        return {"data": cached, "error": None, "source": "Web Search"}

    print(f"   [Events] Fetching from web sources...")
    try:
        results = TOOLS['search_web_events'].invoke({
            "city": city,
            "start_date": start_date,
            "end_date": end_date
        })
        set_cached(cache_key, city, results, start_date, end_date)
        return {"data": results, "error": None, "source": "Web Search"}
    except Exception as e:
        print(f"   [Events] Web error: {e}")
        error_type = "rate_limit" if _is_rate_limit(e) else "error"
        return {"data": [], "error": {"type": error_type, "message": str(e)}, "source": "Web Search"}


@traceable(name="fetch_neighborhoods", run_type="tool", metadata={"category": "dining"})
def fetch_neighborhoods(city: str) -> list:
    """Fetch neighborhoods (internal, no error tracking needed)."""
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
def fetch_restaurants_google(city: str, neighborhoods: list) -> dict:
    """Fetch restaurants from Google Places."""
    cache_key = "restaurants_google"
    cached = get_cached(cache_key, city)
    if cached is not None:
        return {"data": cached, "error": None, "source": "Google Places"}

    print(f"   [Dining] Fetching from Google Places...")
    try:
        results = TOOLS['search_google_places'].invoke({
            "city": city,
            "neighborhoods": neighborhoods or []
        })
        set_cached(cache_key, city, results)
        return {"data": results, "error": None, "source": "Google Places"}
    except Exception as e:
        print(f"   [Dining] Google Places error: {e}")
        error_type = "rate_limit" if _is_rate_limit(e) else "error"
        return {"data": [], "error": {"type": error_type, "message": str(e)}, "source": "Google Places"}


@traceable(name="fetch_restaurants_web", run_type="tool", metadata={"category": "dining"})
def fetch_restaurants_web(city: str, neighborhoods: list) -> dict:
    """Fetch restaurants from web sources (Eater, Infatuation, Reddit)."""
    cache_key = "restaurants_web"
    cached = get_cached(cache_key, city)
    if cached is not None:
        return {"data": cached, "error": None, "source": "Web Search"}

    print(f"   [Dining] Fetching from web sources...")
    try:
        results = TOOLS['search_web_restaurants'].invoke({
            "city": city,
            "neighborhoods": neighborhoods or []
        })
        set_cached(cache_key, city, results)
        return {"data": results, "error": None, "source": "Web Search"}
    except Exception as e:
        print(f"   [Dining] Web error: {e}")
        error_type = "rate_limit" if _is_rate_limit(e) else "error"
        return {"data": [], "error": {"type": error_type, "message": str(e)}, "source": "Web Search"}


@traceable(name="fetch_locations_google", run_type="tool", metadata={"category": "locations"})
def fetch_locations_google(city: str) -> dict:
    """Fetch locations from Google Places."""
    cache_key = "locations_google"
    cached = get_cached(cache_key, city)
    if cached is not None:
        return {"data": cached, "error": None, "source": "Google Places"}

    print(f"   [Locations] Fetching from Google Places...")
    try:
        results = TOOLS['search_google_places_attractions'].invoke({
            "city": city
        })
        set_cached(cache_key, city, results)
        return {"data": results, "error": None, "source": "Google Places"}
    except Exception as e:
        print(f"   [Locations] Google Places error: {e}")
        error_type = "rate_limit" if _is_rate_limit(e) else "error"
        return {"data": [], "error": {"type": error_type, "message": str(e)}, "source": "Google Places"}


@traceable(name="fetch_locations_web", run_type="tool", metadata={"category": "locations"})
def fetch_locations_web(city: str) -> dict:
    """Fetch locations from web sources (Atlas Obscura, Reddit)."""
    cache_key = "locations_web"
    cached = get_cached(cache_key, city)
    if cached is not None:
        return {"data": cached, "error": None, "source": "Web Search"}

    print(f"   [Locations] Fetching from web sources...")
    try:
        results = TOOLS['search_web_locations'].invoke({
            "city": city
        })
        set_cached(cache_key, city, results)
        return {"data": results, "error": None, "source": "Web Search"}
    except Exception as e:
        print(f"   [Locations] Web error: {e}")
        error_type = "rate_limit" if _is_rate_limit(e) else "error"
        return {"data": [], "error": {"type": error_type, "message": str(e)}, "source": "Web Search"}


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

def _extract_data_and_errors(fetch_result: dict, errors_list: list) -> list:
    """Extract data from fetch result and collect any errors."""
    if isinstance(fetch_result, dict) and "data" in fetch_result:
        if fetch_result.get("error"):
            errors_list.append({
                "source": fetch_result.get("source", "Unknown"),
                "type": fetch_result["error"].get("type", "error"),
                "message": fetch_result["error"].get("message", "Unknown error")
            })
        return fetch_result.get("data", [])
    # Backwards compat for functions that return raw lists
    return fetch_result if isinstance(fetch_result, list) else []


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
                fetch_results[name] = {"data": [], "error": {"type": "error", "message": str(e)}, "source": name}

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
                fetch_results[name] = {"data": [], "error": {"type": "error", "message": str(e)}, "source": name}

    # Extract data and collect errors
    concerts_data = _extract_data_and_errors(fetch_results.get("concerts", {}), results["errors"])
    events_tm_data = _extract_data_and_errors(fetch_results.get("events_tm", {}), results["errors"])
    events_web_data = _extract_data_and_errors(fetch_results.get("events_web", {}), results["errors"])
    restaurants_google_data = _extract_data_and_errors(fetch_results.get("restaurants_google", {}), results["errors"])
    restaurants_web_data = _extract_data_and_errors(fetch_results.get("restaurants_web", {}), results["errors"])
    locations_google_data = _extract_data_and_errors(fetch_results.get("locations_google", {}), results["errors"])
    locations_web_data = _extract_data_and_errors(fetch_results.get("locations_web", {}), results["errors"])

    # Phase 2: Aggregation
    print("\n   Phase 2: Aggregating results...")

    # Concerts (no aggregation needed - already clean from Ticketmaster)
    results["concerts"] = concerts_data

    # Events aggregation
    try:
        results["events"] = aggregate_events_data(
            events_tm_data,
            events_web_data,
            city, start_date, end_date
        )
    except Exception as e:
        results["errors"].append({"source": "Events Aggregation", "type": "error", "message": str(e)})
        results["events"] = events_tm_data

    # Dining aggregation
    try:
        results["dining"] = aggregate_restaurants_data(
            restaurants_google_data,
            restaurants_web_data,
            city, neighborhoods
        )
    except Exception as e:
        results["errors"].append({"source": "Dining Aggregation", "type": "error", "message": str(e)})
        results["dining"] = restaurants_google_data

    # Locations aggregation
    try:
        results["locations"] = aggregate_locations_data(
            locations_google_data,
            locations_web_data,
            city
        )
    except Exception as e:
        results["errors"].append({"source": "Locations Aggregation", "type": "error", "message": str(e)})
        results["locations"] = locations_google_data

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
