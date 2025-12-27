# Locations Agent

## Overview

The Locations Agent discovers attractions, hidden gems, and local favorites for a given city by combining Google Places API data with curated web sources like Reddit, Atlas Obscura, and Timeout.

**Focus:** Non-date-specific attractions with emphasis on:
- Local, authentic experiences (not generic tourist traps)
- Hidden gems and underrated spots
- Younger, adventurous traveler vibes

**Location Types Covered:**
- Museums & Art Galleries
- Parks & Gardens
- Landmarks & Historical Sites
- Hidden Gems (from web sources)
- Neighborhoods to Explore
- Unique Local Experiences

**Note:** Unlike Concert and Events agents, Locations are NOT date-specific.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      LOCATIONS AGENT                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. GOOGLE PLACES SEARCH                                         │
│     └─ Search museums, parks, landmarks, attractions            │
│     └─ Dynamic geocoding (works for any city)                   │
│     └─ Filter by rating and review count                        │
│                                                                  │
│  2. WEB SEARCH                                                   │
│     └─ Reddit: Local subreddits for insider tips                │
│     └─ Atlas Obscura: Unusual and hidden spots                  │
│     └─ Timeout: Curated city guides                             │
│     └─ Conde Nast Traveler: Quality recommendations             │
│     └─ Travel + Leisure: Popular attractions                    │
│                                                                  │
│  3. AGGREGATION (Claude Haiku)                                   │
│     └─ Parse web content for location details                   │
│     └─ Prioritize hidden gems and local favorites               │
│     └─ Combine Google Places + Web results                      │
│     └─ Deduplicate by name similarity                           │
│     └─ Sort by rating                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Input: City name (e.g., "San Francisco", "Austin")
         │
         ▼
┌─────────────────────┐
│ Dynamic Geocoding   │──── Nominatim API (free)
│ (any city works)    │     or cached coordinates
└─────────────────────┘
         │
         │ (latitude, longitude)
         ▼
┌─────────────────────┐     ┌─────────────────────┐
│ Google Places       │     │ Web Search          │
│ Search              │     │ (Reddit, Atlas      │
│ (Museums, Parks,    │     │  Obscura, Timeout,  │
│  Landmarks, etc.)   │     │  Travel sites)      │
└─────────────────────┘     └─────────────────────┘
         │                           │
         │ [Structured data]         │ [Page content]
         ▼                           ▼
┌─────────────────────────────────────────────────┐
│              AGGREGATION                         │
│              (Claude Haiku)                      │
│                                                  │
│  • Parse web pages for location details          │
│  • Prioritize hidden gems, local favorites       │
│  • Merge with Google Places data                 │
│  • Deduplicate by name similarity               │
│  • Sort by rating                                │
└─────────────────────────────────────────────────┘
         │
         ▼
Output: List of locations with:
        - name, address, neighborhood
        - category (Museums & Art, Hidden Gems, etc.)
        - rating, description, local_tip
        - website, source
```

## Web Search Sources

Prioritized for younger, local tourist experience:

| Source | Domain | What It Finds |
|--------|--------|---------------|
| Reddit | reddit.com | Local subreddit recommendations, hidden gems |
| Atlas Obscura | atlasobscura.com | Unusual, off-the-beaten-path spots |
| Timeout | timeout.com | Curated city guides, trendy spots |
| Conde Nast Traveler | cntraveler.com | Quality travel recommendations |
| Travel + Leisure | travelandleisure.com | Popular attractions |

**Query Focus:**
- "hidden gems {city}"
- "best things to do {city} locals"
- "underrated spots {city}"
- "cool places to visit {city}"

## Google Places Types Searched

```python
ATTRACTION_TYPES = [
    "tourist_attraction",
    "museum",
    "art_gallery",
    "park",
    "hiking_area",
    "botanical_garden",
    "zoo",
    "aquarium",
    "amusement_park",
    "landmark",
    "historical_landmark",
    "cultural_center",
    "performing_arts_theater",
    "observation_deck",
    "marina",
    "beach",
    "national_park",
    "state_park",
]
```

## Category Classification

Locations are categorized into:

| Category | Types |
|----------|-------|
| Museums & Art | museum, art_gallery, cultural_center |
| Nature & Parks | park, botanical_garden, hiking_area, beach, national_park |
| Wildlife | zoo, aquarium |
| Landmarks | landmark, historical_landmark, observation_deck |
| Entertainment | amusement_park, performing_arts_theater |
| Hidden Gems | Web search results (Reddit, Atlas Obscura) |

## Configuration (`config.py`)

| Setting | Value | Description |
|---------|-------|-------------|
| DEFAULT_SEARCH_RADIUS | 15000m (~10 miles) | Google Places search radius |
| MIN_RATING | 3.5 | Minimum rating (1-5) |
| MIN_REVIEWS | 20 | Minimum review count |
| MAX_RESULTS_PER_TYPE | 10 | Max results per search query |
| MAX_PAGES_TO_EXTRACT | 15 | Web pages to extract |

## Tools

### 1. Google Places Search (`tools/google_places.py`)

**Purpose**: Get structured attraction data from Google Places API

**Searches:**
- Museums and art galleries
- Parks and gardens
- Tourist attractions and landmarks
- Hidden gems and unique places

**Output**: List of location objects with name, address, rating, category, hours

### 2. Web Search (`tools/web_search.py`)

**Purpose**: Find hidden gems and local favorites not on Google

**Sources:**
- Reddit (local subreddits)
- Atlas Obscura (unusual spots)
- Timeout (curated guides)
- Conde Nast Traveler
- Travel + Leisure

### 3. Aggregation (`tools/aggregation.py`)

**Purpose**: Combine and deduplicate results using Claude Haiku

**Process:**
1. Receive Google Places results (structured)
2. Receive web page contents (unstructured)
3. Use Claude Haiku to extract locations from web pages
4. Prioritize hidden gems and local recommendations
5. Merge all results
6. Deduplicate by name similarity
7. Sort by rating

## Usage

```python
from langchain_final.test_agent import run_locations_agent

# Run for a city
result = run_locations_agent("San Francisco")

# Results include:
# - locations: List of location objects
# - total_locations: Count
# - sources: Count by source
# - categories: Count by category
```

## Output Schema

Each location includes:

```json
{
  "name": "Sutro Baths Ruins",
  "address": "Point Lobos Ave, San Francisco, CA",
  "neighborhood": "Lands End",
  "category": "Hidden Gems",
  "description": "Atmospheric ruins of a historic bathhouse with ocean views",
  "rating": 4.7,
  "price": "Free",
  "website": "https://www.nps.gov/goga/planyourvisit/sutro-baths.htm",
  "google_maps_url": "...",
  "source": "atlas_obscura",
  "local_tip": "Visit at sunset for the best photos"
}
```

## Changelog

### 2025-12-26
- Initial implementation
- Created folder structure in langchain_final
- Added dynamic geocoding (works for any city)
- Added Google Places tool for attractions
- Added web search tool (Reddit, Atlas Obscura, Timeout, travel sites)
- Created aggregation tool with Claude Haiku
- Focus on hidden gems and local tourist vibes
