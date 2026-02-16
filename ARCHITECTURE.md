# Weekenders App - Architecture & Documentation

> Multi-agent weekend activity search platform for 100+ US cities

**Live Site:** [weekenderapp.xyz](https://weekenderapp.xyz)
**Backend API:** weekenders-app.onrender.com
**GitHub:** [lelandjfs/weekenders-app](https://github.com/lelandjfs/weekenders-app)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [The Four Agents](#the-four-agents)
5. [External APIs](#external-apis)
6. [Content Filtering & Optimization](#content-filtering--optimization)
7. [Caching Strategy](#caching-strategy)
8. [Deployment](#deployment)
9. [Data Flow Example](#data-flow-example)
10. [Local Development](#local-development)

---

## Overview

Weekenders is a weekend activity discovery platform that aggregates data from multiple sources to help users find:

- **Concerts & Live Music** - From stadium shows to indie venues
- **Dining** - Trendy restaurants, hidden gems, neighborhood favorites
- **Events** - Sports, arts, family activities, festivals
- **Locations** - Hidden gems, parks, museums, local favorites

The platform uses a multi-agent architecture powered by LangChain/LangGraph, with Claude Haiku for intelligent data aggregation and deduplication.

### Key Features

- Search 100+ US cities
- Weekend selection (this weekend, next weekend, custom dates)
- Intelligent deduplication across sources
- 3-day caching for fast repeat queries
- Full observability via LangSmith

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Vercel)                          │
│                   React 19 / Vite / TypeScript                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  WeekenderApp.jsx                                        │   │
│  │  - City search with autocomplete                         │   │
│  │  - Weekend/date selection                                │   │
│  │  - Tabbed results (Concerts, Dining, Events, Locations)  │   │
│  │  - Email subscriptions                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │ POST /search
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND API (Render)                         │
│                FastAPI + Uvicorn + Python 3.13                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  api.py - REST endpoints                                 │   │
│  │  runner.py - Orchestration (parallel fetching)           │   │
│  │  cache.py - Redis caching layer                          │   │
│  │  config.py - Environment & city coordinates              │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┬──────────────┐
          ▼              ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Concert  │  │  Dining  │  │  Events  │  │Locations │
    │  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │
    └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
         │             │             │             │
         └──────┬──────┴──────┬──────┴──────┬──────┘
                │             │             │
          ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐
          │Ticketmaster│ │  Google   │ │  Tavily   │
          │    API    │ │  Places   │ │  Search   │
          └───────────┘ └───────────┘ └───────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Claude Haiku   │
                    │  (Aggregation)  │
                    └─────────────────┘
```

### Processing Pipeline

1. **Request Handling** - FastAPI validates city/dates
2. **Geocoding** - Convert city name to lat/lon (Nominatim)
3. **Parallel Fetching** - ThreadPoolExecutor with 8 workers
4. **Agent Aggregation** - Claude Haiku parses/deduplicates
5. **Response Building** - Structured JSON to frontend

---

## Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| React 19 | UI framework |
| Vite | Build tool |
| Vercel | Hosting & CDN |
| MongoDB | Subscriptions (planned) |

### Backend
| Technology | Purpose |
|------------|---------|
| FastAPI | REST API framework |
| Uvicorn | ASGI server |
| Python 3.13 | Runtime |
| Render | Hosting |

### AI/ML
| Technology | Purpose |
|------------|---------|
| LangChain | Agent framework |
| LangGraph | Workflow orchestration |
| Claude Haiku | Content parsing & aggregation |
| LangSmith | Observability & tracing |

### Data & Caching
| Technology | Purpose |
|------------|---------|
| Redis/Upstash | Caching layer (3-day TTL) |
| Ticketmaster API | Concerts & events |
| Google Places API | Restaurants & locations |
| Tavily API | Web search |

---

## The Four Agents

### 1. Concert Agent

**Purpose:** Find concerts and live music events

**Location:** `Langchain/Concert Agent/`

**Tools:**
- `search_ticketmaster` - Primary concert discovery (25-mile radius)
- `discover_venues` - Find indie/local venues via web search
- `search_web_concerts` - Venue-specific concert searches
- `aggregate_concert_results` - Deduplicate with Claude Haiku

**Data Sources:**
- Ticketmaster Discovery API
- Songkick, Bandsintown (via Tavily)
- Local venue websites

**Output Fields:**
```python
{
  "name": "Artist Name",
  "venue": "Venue Name",
  "date": "2024-02-15",
  "time": "8:00 PM",
  "location": "Austin, TX",
  "price_range": "$45-$120",
  "url": "https://...",
  "source": "ticketmaster",
  "genre": "Rock"
}
```

---

### 2. Dining Agent

**Purpose:** Find restaurants and dining recommendations

**Location:** `Langchain/Dining Agent/`

**Tools:**
- `discover_neighborhoods` - Claude-powered neighborhood identification
- `search_google_places` - Google Places per neighborhood
- `search_web_restaurants` - Eater, Infatuation, Reddit searches
- `aggregate_restaurants` - Deduplicate and rank

**Web Sources:**
- Eater.com (site-specific search)
- The Infatuation
- Reddit r/[city]food

**Filtering Criteria:**
- Minimum rating: 4.0 stars
- Minimum reviews: 50
- Max 5 neighborhoods
- Max 10 results per neighborhood

**Output Fields:**
```python
{
  "name": "Restaurant Name",
  "address": "123 Main St",
  "neighborhood": "East Austin",
  "rating": 4.7,
  "review_count": 342,
  "price_level": "$$",
  "cuisine_type": "Mexican",
  "website": "https://...",
  "google_maps_url": "https://...",
  "source": "google_places"
}
```

---

### 3. Events Agent

**Purpose:** Find sports, arts, family events, and festivals

**Location:** `Langchain/Events Agent/`

**Tools:**
- `search_ticketmaster_events` - Sports, arts, family categories
- `search_web_events` - Eventbrite, Timeout, local event pages
- `aggregate_events` - Parse and deduplicate

**Event Categories:**
- Sports
- Arts & Theatre
- Film
- Family
- Miscellaneous/Festivals

**Output Fields:**
```python
{
  "name": "Event Name",
  "venue": "Venue Name",
  "date": "2024-02-15",
  "time": "14:00",
  "category": "Family",
  "description": "Annual festival...",
  "price_range": "Free",
  "url": "https://...",
  "source": "eventbrite"
}
```

---

### 4. Locations Agent

**Purpose:** Find hidden gems, attractions, and local favorites

**Location:** `Langchain/Locations Agent/`

**Tools:**
- `search_google_places_attractions` - Museums, parks, landmarks
- `search_web_locations` - Reddit hidden gems, Atlas Obscura
- `aggregate_locations` - Categorize and deduplicate

**Attraction Types:**
- Museums & Art
- Nature & Parks
- Landmarks
- Hidden Gems
- Entertainment
- Architecture

**Web Sources:**
- Reddit (r/[city] hidden gems)
- Atlas Obscura
- Timeout
- Condé Nast Traveler
- Travel & Leisure

**Output Fields:**
```python
{
  "name": "Place Name",
  "address": "123 Park Ave",
  "neighborhood": "Downtown",
  "category": "Hidden Gems",
  "description": "A secret rooftop garden...",
  "rating": 4.8,
  "price": "Free",
  "website": "https://...",
  "source": "reddit",
  "local_tip": "Best visited at sunset"
}
```

---

## External APIs

| API | Purpose | Auth | Rate Limit | Cost |
|-----|---------|------|------------|------|
| **Ticketmaster Discovery** | Concerts, events | API Key | 5,000/day | Free |
| **Google Places** | Restaurants, locations | API Key | Varies | $200/mo free credit |
| **Tavily** | Web search | API Key | Varies | Paid tiers |
| **Anthropic Claude** | Aggregation (Haiku) | API Key | Varies | ~$0.0003/query |
| **Nominatim (OSM)** | Geocoding | None | 1/sec | Free |
| **LangSmith** | Observability | API Key | - | Free tier |

### Environment Variables

```bash
# Required
TICKETMASTER_API_KEY=xxx
GOOGLE_PLACES_KEY=xxx
TAVILY_API_KEY=xxx
ANTHROPIC_API_KEY=xxx

# Optional
LANGSMITH_API_KEY=xxx
REDIS_URL=rediss://xxx  # or UPSTASH_REDIS_URL
```

---

## Content Filtering & Optimization

To reduce LLM context usage and costs, we pre-filter web content before sending to Claude Haiku.

### The Problem
Raw web pages contain lots of irrelevant content:
- Navigation menus
- Footers and ads
- Social media links
- Unrelated articles

### The Solution

**Location:** `weekender/content_filter.py`

Pattern-based filters extract only relevant sections:

```python
# Restaurant filter patterns
patterns = [
    r'\*\*[A-Z].*\*\*',           # Bold text (names)
    r'\$+\s*[-–]?\s*\$*',          # Price ranges
    r'\d+(\.\d+)?\s*(stars?|rating)', # Ratings
    r'(address|location|neighborhood)', # Location info
    r'(cuisine|serves?|specializ)', # Cuisine type
    # ... more patterns
]
```

### Content Types

| Type | Filter Function | Use Case |
|------|-----------------|----------|
| `restaurants` | `filter_restaurant_content()` | Dining Agent |
| `events` | `filter_event_content()` | Events Agent |
| `locations` | `filter_location_content()` | Locations Agent |
| `concerts` | `filter_concert_content()` | Concert Agent |

### Performance Impact

- **Context reduction:** 30-80% depending on page
- **Batch processing:** 3 pages per batch, 3 parallel workers
- **Cost savings:** ~60% reduction in Haiku tokens

### Usage

```python
from content_filter import filter_content, batch_pages

# Filter a single page
filtered = filter_content(raw_html, 'restaurants', max_lines=100)

# Batch multiple pages
batches = batch_pages(filtered_pages, batch_size=3)
```

---

## Caching Strategy

**Location:** `weekender/cache.py`

### Cache Backend
- **Production:** Upstash Redis (SSL)
- **Development:** Local Redis (localhost:6379)
- **Fallback:** Graceful degradation if unavailable

### Cache Keys

```
Format: weekender:{prefix}:{city}:{start_date}:{end_date}

Examples:
- weekender:concerts:austin:2024-02-15:2024-02-17
- weekender:dining:san_francisco
- weekender:neighborhoods:chicago
```

### TTL
All cached data expires after **3 days**.

### Cached Data Types

| Prefix | Data | Agent |
|--------|------|-------|
| `concerts` | Ticketmaster concerts | Concert |
| `events_tm` | Ticketmaster events | Events |
| `events_web` | Web-scraped events | Events |
| `restaurants_google` | Google Places | Dining |
| `restaurants_web` | Web restaurants | Dining |
| `neighborhoods` | Discovered neighborhoods | Dining |
| `locations_google` | Google attractions | Locations |
| `locations_web` | Web locations | Locations |

### Cache Functions

```python
# Get cached data
data = get_cached("concerts", "austin", "2024-02-15", "2024-02-17")

# Set cached data
set_cached("concerts", "austin", concerts_list, "2024-02-15", "2024-02-17")

# Clear cache
clear_cache(city="austin")  # City-specific
clear_cache()               # All cache
```

---

## Deployment

### Frontend (Vercel)

**URL:** weekenderapp.xyz

```bash
# Build
cd frontend
npm run build

# Deploy (automatic on git push)
git push origin main
```

**Configuration:**
- Build command: `vite build`
- Output directory: `dist`
- Auto-deploy: Enabled

### Backend (Render)

**URL:** weekenders-app.onrender.com

**Procfile:**
```
web: uvicorn api:app --host 0.0.0.0 --port $PORT
```

**Configuration:**
- Runtime: Python 3.13
- Build: `pip install -r requirements.txt`
- Auto-deploy: Enabled (on git push)

### Environment Setup (Render)

1. Create Web Service
2. Connect GitHub repo
3. Set root directory: `weekender`
4. Add environment variables
5. Deploy

---

## Data Flow Example

### Search: "Austin" + "This Weekend"

```
1. User Input
   └─→ POST /search { city: "Austin", weekend: "this" }

2. Geocoding
   └─→ get_coordinates("austin") → (30.2672, -97.7431)

3. Date Calculation
   └─→ get_weekend_dates("this") → (2024-02-15, 2024-02-17)

4. Parallel Phase 1 (8 workers)
   ├─→ fetch_concerts(Ticketmaster) → 25 concerts
   ├─→ fetch_events_ticketmaster() → 15 events
   ├─→ fetch_events_web(Tavily) → 8 web events
   ├─→ discover_neighborhoods() → [Downtown, East Austin, South Congress, ...]
   ├─→ fetch_restaurants_google() → 40 restaurants
   ├─→ fetch_restaurants_web() → 20 web restaurants
   ├─→ fetch_locations_google() → 30 attractions
   └─→ fetch_locations_web() → 15 hidden gems

5. Phase 2 - Aggregation
   ├─→ aggregate_events() → 18 unique events
   ├─→ aggregate_restaurants() → 35 unique restaurants
   └─→ aggregate_locations() → 28 unique locations

6. Response
   {
     "city": "Austin",
     "start_date": "2024-02-15",
     "end_date": "2024-02-17",
     "concerts": [...],    // 25 concerts
     "dining": [...],      // 35 restaurants
     "events": [...],      // 18 events
     "locations": [...],   // 28 locations
     "errors": []
   }
```

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis (optional, for caching)

### Backend Setup

```bash
# Clone repo
git clone https://github.com/lelandjfs/weekenders-app.git
cd weekenders-app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r weekender/requirements.txt

# Set environment variables
export TICKETMASTER_API_KEY=xxx
export GOOGLE_PLACES_KEY=xxx
export TAVILY_API_KEY=xxx
export ANTHROPIC_API_KEY=xxx

# Run backend
cd weekender
uvicorn api:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Testing

```bash
# Test API
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"city": "Austin", "weekend": "this"}'

# Test cache status
curl http://localhost:8000/cache-status
```

---

## Project Structure

```
weekenders_app/
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── WeekenderApp.jsx    # Main component
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── weekender/                   # FastAPI backend
│   ├── api.py                  # REST endpoints
│   ├── runner.py               # Orchestration
│   ├── cache.py                # Redis caching
│   ├── config.py               # Environment config
│   ├── content_filter.py       # Pre-filtering
│   ├── requirements.txt
│   └── Procfile
│
├── Langchain/                   # LangChain agents
│   ├── Concert Agent/
│   │   ├── concert_agent.py
│   │   ├── config.py
│   │   └── tools/
│   │       ├── ticketmaster.py
│   │       ├── tavily_search.py
│   │       └── aggregation.py
│   │
│   ├── Dining Agent/
│   │   ├── dining_agent.py
│   │   └── tools/
│   │       ├── google_places.py
│   │       ├── web_search.py
│   │       ├── neighborhood_discovery.py
│   │       └── aggregation.py
│   │
│   ├── Events Agent/
│   │   └── tools/
│   │       ├── ticketmaster.py
│   │       ├── web_search.py
│   │       └── aggregation.py
│   │
│   └── Locations Agent/
│       └── tools/
│           ├── google_places.py
│           ├── web_search.py
│           └── aggregation.py
│
└── ARCHITECTURE.md              # This file
```

---

## Future Improvements

- [ ] User accounts and saved searches
- [ ] Email subscriptions for weekend updates
- [ ] More cities (international)
- [ ] Price filtering
- [ ] Distance/neighborhood filtering
- [ ] Mobile app (React Native)
- [ ] Personalized recommendations

---

## License

MIT License - See LICENSE file

---

*Built with LangChain, Claude, and way too much coffee.*
