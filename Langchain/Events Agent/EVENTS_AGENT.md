# Events Agent

## Overview

The Events Agent discovers non-music events for a given city and date range by combining Ticketmaster API data with web sources like Eventbrite and Timeout.

**Event Types Covered:**
- Sports (NBA, NFL, NHL, etc.)
- Arts & Theatre (plays, musicals, dance)
- Comedy shows
- Family events (Jurassic Quest, Disney on Ice)
- Festivals
- Film screenings
- Community events

**Note:** Concerts/music events are handled by the Concert Agent, not this agent.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        EVENTS AGENT                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. TICKETMASTER SEARCH                                          │
│     └─ Search Sports, Arts & Theatre, Family classifications    │
│     └─ Dynamic geocoding (works for any city)                   │
│     └─ Filter by date range (Fri-Sun)                           │
│                                                                  │
│  2. WEB SEARCH                                                   │
│     └─ Eventbrite: Local event listings                         │
│     └─ Timeout: Curated city events                             │
│     └─ General: "things to do this weekend" queries             │
│                                                                  │
│  3. AGGREGATION (Claude Haiku)                                   │
│     └─ Parse web content for event details                      │
│     └─ Combine Ticketmaster + Web results                       │
│     └─ Deduplicate by event name + venue + date                 │
│     └─ Sort by date                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Input: City name + Weekend (e.g., "Sacramento", "next")
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
│ Ticketmaster        │     │ Web Search          │
│ Search              │     │ (Eventbrite,        │
│ (Sports, Arts,      │     │  Timeout, general)  │
│  Theatre, Family)   │     │                     │
└─────────────────────┘     └─────────────────────┘
         │                           │
         │ [Structured data]         │ [Page content]
         ▼                           ▼
┌─────────────────────────────────────────────────┐
│              AGGREGATION                         │
│              (Claude Haiku)                      │
│                                                  │
│  • Parse web pages for event details             │
│  • Merge with Ticketmaster data                  │
│  • Deduplicate by name + venue + date           │
│  • Sort by date                                  │
└─────────────────────────────────────────────────┘
         │
         ▼
Output: List of events with:
        - name, venue, date, time
        - category (Sports, Arts, Family, etc.)
        - price_range, url, source
```

## Date Range

**Events Agent uses Friday - Sunday** (unlike Concert Agent which uses Thu-Sat)

| Agent | Date Range | Rationale |
|-------|------------|-----------|
| Concert Agent | Thu - Sat | Concerts peak Thu-Sat nights |
| Events Agent | Fri - Sun | Family/daytime events include Sunday |

## Dynamic Geocoding

The agent can find coordinates for **any city** dynamically:

1. **Cache lookup first** - Common cities (SF, NYC, LA, etc.) are cached
2. **Nominatim fallback** - Uses OpenStreetMap's free geocoding API for any other city

```python
# Works for any city:
result = run_events_agent("Sacramento")      # Not in original cache
result = run_events_agent("Boise, Idaho")    # Looked up dynamically
result = run_events_agent("San Diego")       # Works fine
```

## Tools

### 1. Ticketmaster Search (`tools/ticketmaster.py`)

**Purpose**: Get structured event data from Ticketmaster API

**Classifications Searched:**
- Sports (NBA, NFL, NHL, MLB, etc.)
- Arts & Theatre (plays, musicals, dance, opera)
- Family (kids shows, exhibitions)

**Output**: List of event objects with venue, date, time, prices, URLs

### 2. Web Search (`tools/web_search.py`)

**Purpose**: Find local events not on Ticketmaster

**Sources:**
| Source | Domain | What It Finds |
|--------|--------|---------------|
| Eventbrite | eventbrite.com | Local community events, festivals |
| Timeout | timeout.com | Curated "things to do" guides |
| General | (no domain filter) | Weekend event roundups |

### 3. Aggregation (`tools/aggregation.py`)

**Purpose**: Combine and deduplicate results using Claude Haiku

**Process:**
1. Receive Ticketmaster results (structured)
2. Receive web page contents (unstructured)
3. Use Claude Haiku to parse web pages
4. Merge all results
5. Deduplicate by event name + venue + date
6. Sort by date

## Configuration (`config.py`)

| Setting | Value | Description |
|---------|-------|-------------|
| DEFAULT_SEARCH_RADIUS | 25 miles | Ticketmaster search radius |
| TICKETMASTER_RESULTS_LIMIT | 50 | Max results per classification |
| MAX_PAGES_TO_EXTRACT | 15 | Web pages to extract |

## Test Results

### San Francisco (2025-12-26)
- **Date Range**: Jan 2-4, 2026 (Fri-Sun)
- **Total Events**: 17
- **Sources**: Ticketmaster (15), Eventbrite (1), Timeout (1)
- **Categories**: Arts & Theatre (12), Sports (2), Family (1), Festival (1)
- **Top Events**: Warriors game, Shen Yun, comedy shows, magic shows

### Sacramento (2025-12-26)
- **Date Range**: Jan 2-4, 2026 (Fri-Sun)
- **Total Events**: 10
- **Sources**: Ticketmaster (7), Eventbrite (3)
- **Categories**: Sports (2), Arts & Theatre (3), Family (2), Cultural (1)
- **Top Events**: Kings game, Jurassic Quest, comedy shows, Kwanzaa celebration

## Usage

```python
from langchain_final.test_agent import run_events_agent

# Run for a city
result = run_events_agent("San Francisco")

# Or with specific weekend
result = run_events_agent("Sacramento", weekend="this")

# Results include:
# - events: List of event objects
# - total_events: Count
# - sources: Count by source
# - categories: Count by category
```

## Changelog

### 2025-12-26
- Initial implementation
- Created folder structure in langchain_final
- Added dynamic geocoding (works for any city)
- Added Ticketmaster tool for Sports, Arts, Family events
- Added web search tool (Eventbrite, Timeout)
- Created aggregation tool with Claude Haiku
- Tested SF and Sacramento successfully
