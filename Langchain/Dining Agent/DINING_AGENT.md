# Dining Agent

## Overview

The Dining Agent discovers restaurant recommendations for a given city by combining multiple data sources to provide comprehensive, high-quality suggestions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DINING AGENT                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. NEIGHBORHOOD DISCOVERY                                       │
│     └─ Find trendy/foodie neighborhoods via web search          │
│                                                                  │
│  2. GOOGLE PLACES SEARCH                                         │
│     └─ Search each neighborhood for highly-rated restaurants    │
│     └─ Filter by rating (≥4.0) and reviews (≥50)               │
│                                                                  │
│  3. WEB SEARCH (Curated Sources)                                │
│     └─ Eater: City guides, best-of lists                        │
│     └─ The Infatuation: Curated reviews                         │
│     └─ Reddit: Local recommendations                            │
│                                                                  │
│  4. AGGREGATION (Claude Haiku)                                   │
│     └─ Parse web content for restaurant details                 │
│     └─ Combine Google Places + Web results                      │
│     └─ Deduplicate by name + address                            │
│     └─ Rank by rating, review count, and mentions               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Input: City name (e.g., "San Francisco")
         │
         ▼
┌─────────────────────┐
│ Neighborhood        │
│ Discovery           │──────────────────────────────────┐
│ (Tavily Search)     │                                  │
└─────────────────────┘                                  │
         │                                               │
         │ ["Mission", "Hayes Valley", "North Beach"...] │
         ▼                                               │
┌─────────────────────┐     ┌─────────────────────┐     │
│ Google Places       │     │ Web Search          │     │
│ Search              │     │ (Eater, Reddit,     │◄────┘
│ (per neighborhood)  │     │  Infatuation)       │
└─────────────────────┘     └─────────────────────┘
         │                           │
         │ [Structured data]         │ [Page content]
         ▼                           ▼
┌─────────────────────────────────────────────────┐
│              AGGREGATION                         │
│              (Claude Haiku)                      │
│                                                  │
│  • Parse web pages for restaurant details        │
│  • Merge with Google Places data                 │
│  • Deduplicate by name similarity               │
│  • Rank and sort results                        │
└─────────────────────────────────────────────────┘
         │
         ▼
Output: List of restaurants with:
        - name, address, neighborhood
        - rating, review_count
        - price_level, cuisine_type
        - website, source
```

## Tools

### 1. Neighborhood Discovery (`tools/neighborhood_discovery.py`)

**Purpose**: Find the best food neighborhoods in a city before searching for restaurants.

**Why**: Searching city-wide returns generic results. Targeting trendy neighborhoods yields better recommendations.

**Process**:
1. Search Tavily with Reddit-focused queries (locals know best)
2. Use Claude Haiku to extract neighborhood names from search results
3. Return top 5 neighborhoods

**Queries**:
- "best food neighborhoods {city} site:reddit.com"
- "trendy neighborhoods {city} site:reddit.com"
- "foodie neighborhoods {city}"
- "best neighborhoods to eat {city}"

**Output**: List of 5 neighborhood names (e.g., Mission, Hayes Valley, Inner Sunset)

### 2. Google Places Search (`tools/google_places.py`)

**Purpose**: Get highly-rated restaurants with structured data.

**API**: Google Places API (New) - Text Search endpoint

**Filters**:
- Minimum rating: 4.0
- Minimum reviews: 50

**Fields Retrieved**:
- displayName, formattedAddress
- rating, userRatingCount
- priceLevel, types/primaryType
- websiteUri, googleMapsUri
- regularOpeningHours

**Output**: List of restaurant objects with structured data

### 3. Web Search (`tools/web_search.py`)

**Purpose**: Get curated recommendations from food experts and locals.

**Sources**:
| Source | Domain | Why |
|--------|--------|-----|
| Eater | eater.com | Professional food journalism, city guides |
| Infatuation | theinfatuation.com | Curated, opinionated reviews |
| Reddit | reddit.com | Authentic local recommendations |

**Process**:
1. Search each source with city + neighborhood queries
2. Filter to article URLs (not homepages)
3. Extract full page content via Tavily
4. Return markdown content for parsing

### 4. Aggregation (`tools/aggregation.py`)

**Purpose**: Combine and deduplicate results using Claude Haiku.

**Why Claude**: Web pages have inconsistent formats. LLM can intelligently extract restaurant details from messy markdown.

**Process**:
1. Receive Google Places results (structured)
2. Receive web page contents (unstructured)
3. Use Claude Haiku to parse web pages
4. Merge all results
5. Deduplicate by restaurant name + address similarity
6. Return unified list

## Configuration (`config.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| MAX_NEIGHBORHOODS | 5 | Neighborhoods to discover |
| MIN_RATING | 4.0 | Minimum Google rating |
| MIN_REVIEWS | 50 | Minimum review count |
| MAX_RESULTS_PER_NEIGHBORHOOD | 10 | Google results per hood |
| MAX_PAGES_TO_EXTRACT | 15 | Web pages to extract |

## Test Output Structure

Tests are saved with timestamps to preserve history:

```
tests/
└── San_Francisco/
    └── run_20251225_140000.json
    └── run_20251225_150000.json
└── Austin/
    └── run_20251225_141500.json
```

Each run creates a new file, never overwriting previous results.

## Usage

```python
from dining_agent import DiningAgent

agent = DiningAgent()
results = agent.run("San Francisco")

# Results include:
# - restaurants: List of restaurant objects
# - neighborhoods: Discovered neighborhoods
# - sources: Count by source (google_places, eater, reddit, etc.)
```

## Rating Scales

**Important**: Different sources use different rating scales:

| Source | Scale | Notes |
|--------|-------|-------|
| Google Places | 1-5 | Standard 5-star rating |
| The Infatuation | 1-10 | Higher = better |
| Eater | N/A | Usually no numeric rating |
| Reddit | N/A | Recommendations, no rating |

Results are sorted by rating descending. Infatuation's 10-scale means their top picks (9+) will appear before Google's 4.8 restaurants.

## Test Results

### San Francisco (2025-12-25)
- **Neighborhoods Found**: Mission District, Emeryville, and others
- **Total Restaurants**: 49
- **Google Places**: 41 restaurants
- **Infatuation**: 8 restaurants
- **Top Picks**: San Ho Won (9.5), Californios (9.3), Bodega SF (9.2)

## Changelog

### 2025-12-25
- Initial implementation
- Created folder structure
- Added neighborhood discovery tool
- Added Google Places search tool
- Added web search tool (Eater, Reddit, Infatuation)
- Created aggregation tool with Claude Haiku
- Created main dining_agent.py orchestration
- Created test_dining_agent.py with timestamp-based output
- First successful test run for San Francisco (49 restaurants)
- **Fixed neighborhood discovery**: Replaced brittle regex with Claude Haiku extraction
- **Added Reddit as primary source** for neighborhood discovery (locals give best recommendations)
- Created this documentation
