# Weekenders App - Comprehensive Planning Document & Feasibility Analysis

**Document Last Updated: November 28, 2024 - Added Context Router for intelligent city-based search strategies, UI-agnostic, removed Spotify OAuth personalization, focused on specific API sources, updated web search strategy, caching optional for v1**

## Executive Summary

### High-level Overview
The Weekenders App is a UI-agnostic multi-agent AI system that aggregates location-based events and recommendations for specific date ranges. The system is designed as a data engine with LangChain integration, capable of serving various front-ends (desktop app, email automation, mobile, web, etc.).

**V1 Simplification**: The system retrieves ALL concerts and events in a given geography/date range without user personalization. Spotify integration for personalized recommendations is deferred to v2.

### Key Value Proposition
- **Context-Aware Search**: Intelligently adapts search strategy based on city size and characteristics (NYC uses neighborhoods, smaller cities search city-wide)
- **Comprehensive Event Discovery**: Aggregates ALL concerts, dining, events, and attractions in a location
- **UI-Agnostic Architecture**: Data engine can power multiple interfaces - mobile apps, desktop apps, email automation, web services
- **Multi-Source Synthesis**: Sub-agent architecture combines multiple data sources for comprehensive coverage
- **Time-Based Relevance**: Focuses on specific date ranges, perfect for weekend planning or trip planning
- **AI-Powered Orchestration**: LangChain/LangGraph integration with intelligent routing and data aggregation
- **Simplified v1 Scope**: No OAuth complexity, focus on geographic event discovery

## Architecture Overview

### System Diagram Description (Text-Based)
```
User Input Layer
    └── [Date Range + Location Selection]
            │
    ┌───────▼───────────────────────────┐
    │   CONTEXT ROUTER (LLM-Powered)    │
    │   - Analyzes city characteristics │
    │   - Determines search strategy    │
    │   - Sets API parameters           │
    │   - Identifies neighborhoods      │
    └───────┬───────────────────────────┘
            │
    ┌───────▼───────────────────────────┐
    │   Search Context Object           │
    │   {                               │
    │     city_type: "large_metro",     │
    │     neighborhoods: [...],         │
    │     search_radius: {...},         │
    │     strategy: {...}               │
    │   }                               │
    └───────┬───────────────────────────┘
            │
    ┌───────▼───────────────────────────┐
    │   LangGraph Orchestration Layer   │
    └───────┬───────────────────────────┘
            │
    Main Agent Layer (Parallel Execution)
    ├── Concert Agent
    │   ├── Ticketmaster Sub-Agent ◄── Ticketmaster Discovery API (FREE)
    │   ├── SeatGeek Sub-Agent ◄── SeatGeek API (FREE*)
    │   └── Web Search Sub-Agent ◄── Bandsintown, Local Sources
    │
    ├── Dining Agent
    │   ├── Google Places Sub-Agent ◄── Google Places API (FREE CREDIT)
    │   └── Web Search Sub-Agent ◄── Eater, Reddit, Infatuation
    │
    ├── Events Agent
    │   ├── Ticketmaster Sub-Agent ◄── Ticketmaster Discovery API (FREE)
    │   ├── SeatGeek Sub-Agent ◄── SeatGeek API (FREE*)
    │   └── Web Search Sub-Agent ◄── Eventbrite, Local Event Sources
    │
    └── Locations Agent
        ├── Google Places Sub-Agent ◄── Google Places API (FREE CREDIT)
        └── Web Search Sub-Agent ◄── Timeout, Atlas Obscura, Tourism Sites
            │
    ┌───────▼───────────────────────────┐
    │   Synthesis Agent                 │
    │   - Multi-source aggregation      │
    │   - Intelligent deduplication     │
    │   - Priority ranking              │
    │   - Output formatting             │
    └───────┬───────────────────────────┘
            │
    ┌───────▼───────────────────────────┐
    │   Output Interface Layer          │
    │   - JSON/structured output        │
    │   - UI-agnostic format            │
    │   - Ready for any frontend        │
    └───────────────────────────────────┘

    Note: V1 has NO caching layer - all queries are real-time
          Caching (MongoDB) can be added in V2 if needed
```

### Agent Workflow and Data Flow
1. **User Input**: User provides location and date range parameters (either manual selection or automated schedule)
2. **Context Routing (LLM-Powered)**:
   - Analyzes city characteristics (size, population, geography)
   - Determines if neighborhood-based strategy is needed (large cities like NYC) vs city-wide (smaller cities like Kyoto)
   - Identifies trendy/popular neighborhoods for large metros
   - Sets appropriate search radii for different query types
   - Cost: ~$0.0002 per query (GPT-4o-mini)
3. **Parallel Agent Execution**: All data-gathering agents run concurrently using context parameters
4. **Data Collection**: Each agent queries its respective APIs/sources (real-time, no caching) with context-aware parameters
5. **Synthesis**: Results are aggregated, deduplicated, and formatted
6. **Delivery**: Formatted output presented as JSON/structured data (UI-agnostic)

### Agent Interaction Pattern
The system uses **LangGraph State Management** with:
- Context Router sets shared state with search parameters
- Main agents execute in parallel, reading from shared context
- Each specialized agent is a node in the graph
- Synthesis agent aggregates results from all agents
- State flows through the graph maintaining context

## Context Router Specification

### Purpose and Architecture

The **Context Router** is an LLM-powered pre-processing layer that analyzes the user's location input and intelligently determines the optimal search strategy before any data agents execute.

**Key Problem Solved**: Different cities require different search strategies. Searching for "restaurants in NYC" yields overwhelming, unfocused results. But breaking NYC into neighborhoods (Williamsburg, Lower East Side, etc.) with targeted searches produces better, more curated recommendations. Smaller cities like Kyoto or Austin don't need this complexity.

### Input/Output Specification

**Input:**
- `location`: String (e.g., "New York City", "Austin, Texas", "Kyoto, Japan")
- `start_date`: ISO date string
- `end_date`: ISO date string

**Output (Context Object):**
```python
{
  "location": "New York City",
  "city_type": "large_metro",  # or "medium_city", "small_town"
  "population_tier": "mega",    # or "large", "medium", "small"
  "needs_neighborhood_strategy": True,
  "neighborhoods": [
    "Williamsburg, Brooklyn",
    "Lower East Side, Manhattan",
    "Astoria, Queens",
    "Greenpoint, Brooklyn",
    "East Village, Manhattan"
  ],
  "search_parameters": {
    "dining_radius_miles": 1.5,
    "concert_radius_miles": 25,
    "events_radius_miles": 15,
    "locations_radius_miles": 2
  },
  "strategy": {
    "dining": "neighborhood_targeted",     # or "city_wide"
    "concerts": "city_wide",               # always city-wide
    "events": "city_wide",                 # always city-wide
    "locations": "neighborhood_targeted"   # or "city_wide"
  }
}
```

### LLM Decision Logic

The Context Router uses GPT-4o-mini (cost: ~$0.0002/query) with the following prompt logic:

**City Type Classification:**
- **Large Metro** (NYC, LA, Tokyo, London): Pop > 5M, needs neighborhoods
- **Medium City** (Austin, Portland, Kyoto): Pop 500K-5M, city-wide search
- **Small Town** (< 500K): Simple city-wide search

**Neighborhood Selection Criteria** (for large metros only):
- Identifies 3-5 trendy/popular neighborhoods known for dining/nightlife
- Prioritizes areas with high concentration of restaurants/attractions
- Balances geographic diversity (different boroughs/districts)
- Uses current knowledge of popular areas (not static list)

**Search Radius Logic:**
- **Large Metro**: Tight radius (1-2 miles) to avoid overwhelming results
- **Medium City**: Medium radius (3-5 miles) for good coverage
- **Small Town**: Wide radius (5-10 miles) to ensure sufficient results
- **Concerts**: Always wider radius (15-25 miles) - people travel for shows

### Strategy Examples

**Example 1: New York City**
```python
{
  "city_type": "large_metro",
  "needs_neighborhood_strategy": True,
  "neighborhoods": [
    "Williamsburg, Brooklyn",
    "Lower East Side, Manhattan",
    "Astoria, Queens",
    "Greenpoint, Brooklyn"
  ],
  "search_parameters": {
    "dining_radius_miles": 1.5,
    "concert_radius_miles": 25,
    "locations_radius_miles": 2
  },
  "strategy": {
    "dining": "neighborhood_targeted",
    "locations": "neighborhood_targeted",
    "concerts": "city_wide",
    "events": "city_wide"
  }
}
```
**Impact**: Dining Agent searches 4 neighborhoods with 1.5-mile radius each, yielding ~20-30 high-quality restaurants instead of 500+ unfocused results.

**Example 2: Austin, Texas**
```python
{
  "city_type": "medium_city",
  "needs_neighborhood_strategy": False,
  "neighborhoods": None,
  "search_parameters": {
    "dining_radius_miles": 5,
    "concert_radius_miles": 20,
    "locations_radius_miles": 5
  },
  "strategy": {
    "dining": "city_wide",
    "locations": "city_wide",
    "concerts": "city_wide",
    "events": "city_wide"
  }
}
```
**Impact**: All agents search city-wide with appropriate radius for good coverage.

**Example 3: Kyoto, Japan**
```python
{
  "city_type": "medium_city",
  "needs_neighborhood_strategy": False,
  "search_parameters": {
    "dining_radius_miles": 5,
    "concert_radius_miles": 15,
    "locations_radius_miles": 6
  },
  "strategy": {
    "dining": "city_wide",
    "locations": "city_wide",
    "concerts": "city_wide",
    "events": "city_wide"
  }
}
```

### Feasibility Assessment

**Pros:**
- ✅ Dramatically improves result quality for large cities
- ✅ Prevents overwhelming user with 500+ restaurants in NYC
- ✅ Minimal cost (~$0.0002 per query)
- ✅ Flexible - LLM adapts to new cities without hardcoded rules
- ✅ Future-proof - neighborhoods change, LLM stays current

**Cons:**
- ⚠️ Adds one LLM dependency (but cheap and non-critical)
- ⚠️ Slight latency increase (~500-800ms for routing)
- ⚠️ Requires OpenAI API key

**Alternatives Considered:**
1. **Hardcoded city rules** - Not scalable, becomes stale
2. **No routing** - Poor UX for large cities
3. **User selects neighborhoods** - Extra friction, users don't know neighborhoods

**Recommendation:** Implement Context Router for V1. The quality improvement for large cities justifies minimal cost and complexity.

## Date Range Specifications by Agent

Each agent has specific date range logic based on the nature of its content:

| Agent | Date Range | Days | Rationale |
|-------|-----------|------|-----------|
| **Concert Agent** | Thu - Sat | 3 days | Concerts peak Thu-Sat nights |
| **Events Agent** | Fri - Sun | 3 days | General events include Sunday activities |
| **Dining Agent** | Fri - Sun | 3 days | Weekend dining, including Sunday brunch |
| **Locations Agent** | Fri - Sun | 3 days | Attractions open all weekend |

**Weekend Calculation Logic:**
- "Next weekend" = the upcoming Saturday's week (not this week if today is Mon-Wed)
- "This weekend" = the current week's Sat (if today is Thu-Sun)
- All date calculations use the `get_weekend_dates()` utility function

## Individual Agent Specifications

### 1. Concert Agent

**Purpose and Scope**
- Retrieve ALL concerts in target location during date range
- No personalization in v1 (Spotify integration deferred to v2)
- Aggregate data from multiple sources for comprehensive coverage

**Date Range Logic**
- Concert Agent uses **Thursday through Saturday** of the target weekend
- Rationale: Concerts are typically Thu-Sat evening events; Sunday shows are less common
- "Next weekend" calculation: Find the upcoming Saturday, then include Thu-Sat of that week
- Example: If today is Wednesday Dec 25, "next weekend" = Jan 2 (Thu) - Jan 4 (Sat)

**Required Data Sources and APIs**
- Ticketmaster Discovery API for concert listings (FREE - 5,000 calls/day)
- Tavily web search + extract for indie venues (Bandsintown, local sources)
- Note: SeatGeek deferred (verification pending)

**Input/Output Specification**
- Input: Location, weekend identifier (e.g., "next", "this", or specific date)
- Output: Array of concert objects with artist, venue, date, ticket URL

**Feasibility Assessment**
- ✅ Ticketmaster API offers comprehensive event search
- ✅ SeatGeek provides additional coverage with free tier
- ✅ No OAuth complexity in v1

**Potential Challenges**
- API rate limits (Ticketmaster: 5,000/day)
- Deduplication across sources
- Bandsintown API is artist-centric, not location-based

### 2. Dining Agent

**Purpose and Scope**
- Find highly rated restaurants in target area
- Aggregate recommendations from multiple sources
- Combine API data with curated web content

**Required Data Sources and APIs**
- Google Places API (Currently $200/month credit, changing March 2025)
- Web search for curated recommendations (Eater, Reddit, The Infatuation)
- Note: Yelp API only has 30-day trial, OpenTable is partner-only

**Input/Output Specification**
- Input: Location, date range, optional cuisine preferences
- Output: Array of restaurant objects with name, rating, cuisine, price range, reviews

**Feasibility Assessment**
- ✅ Google Places API provides good coverage with current credit
- ✅ Web search can supplement with quality recommendations
- ❌ Yelp becomes expensive after trial ($229+/month)
- ❌ OpenTable requires partnership approval

**Potential Challenges**
- Google Places pricing changes in March 2025
- Limited access to reservation systems
- Balancing API data with curated content

### 3. Sports Agent (Merged into Events Agent for v1)

**Note**: Sports events are handled by the Events Agent through Ticketmaster and SeatGeek APIs, which both provide comprehensive sports coverage. A dedicated Sports Agent is deferred to v2.

### 4. Events Agent

**Purpose and Scope**
- Compile ALL events including sports, festivals, theater, comedy, family events
- Focus on time-specific events in the given date range
- Aggregate from multiple sources for comprehensive coverage

**Required Data Sources and APIs**
- Ticketmaster Discovery API (FREE - 5,000 calls/day, covers sports/arts/entertainment)
- SeatGeek API (FREE with attribution, strong sports/entertainment coverage)
- Web search for local events (Eventbrite listings, Facebook events, local calendars)
- Note: AllEvents API requires $500+/month minimum

**Input/Output Specification**
- Input: Location, date range, optional event categories
- Output: Array of events with name, type, date, venue, description, ticket URL

**Feasibility Assessment**
- ✅ Ticketmaster provides comprehensive event coverage
- ✅ SeatGeek adds additional coverage with category filtering
- ✅ Web search fills gaps for local/community events
- ❌ AllEvents API too expensive for personal use

**Potential Challenges**
- Event deduplication across sources
- Rate limits when searching multiple categories
- Local event discovery requires web search

### 5. Locations Agent

**Purpose and Scope**
- Non-time-limited attractions (museums, tours, landmarks)
- Unique local businesses and experiences
- Points of interest and activities

**Required Data Sources and APIs**
- Google Places API for attractions (Currently $200/month credit)
- Web search for curated content (Timeout, Atlas Obscura, local tourism sites)
- Note: Viator API is partner-only, not publicly available

**Input/Output Specification**
- Input: Location, interest categories
- Output: Array of attractions with name, type, hours, description, reviews

**Feasibility Assessment**
- ✅ Google Places provides comprehensive attraction data
- ✅ Web search can access curated content
- ❌ Viator API requires partnership approval
- ❌ TripAdvisor API not publicly available

**Potential Challenges**
- Limited APIs for tour/activity booking
- Quality vs. quantity balance
- Reliance on web search for curated recommendations

### 6. Synthesis Agent

**Purpose and Scope**
- Aggregate outputs from all agents
- Remove duplicates and conflicts
- Format into user-friendly structure
- Apply intelligent ranking/prioritization

**Required Data Sources and APIs**
- Internal only (receives data from other agents)

**Input/Output Specification**
- Input: Arrays from all five data agents
- Output: Structured, deduplicated, formatted recommendations

**Feasibility Assessment**
- ✅ Technically straightforward
- ✅ LangChain provides good orchestration tools

**Potential Challenges**
- Deduplication logic complexity
- Handling conflicting information
- Intelligent prioritization algorithms

## API & Data Source Research (Updated November 2024 - V1 Focus)

### Concert Agent APIs

#### Ticketmaster Discovery API ✅ FREE TIER CONFIRMED
- **Capabilities**: Search concerts by location, date range, genre; 230,000+ events
- **Authentication**: API key required (instant upon registration)
- **Rate Limits**: 5,000 calls/day, 5 requests/second
- **Cost**: FREE for personal use
- **Coverage**: US, Canada, Mexico, Australia, NZ, UK, Ireland, Europe
- **Documentation**: https://developer.ticketmaster.com
- **V1 Status**: PRIMARY SOURCE

#### SeatGeek API ✅ FREE FOR PERSONAL USE (UNCONFIRMED)
- **Capabilities**: Events by location, performers, venues, recommendations
- **Authentication**: Client ID required
- **Rate Limits**: Not publicly documented
- **Cost**: Appears free for personal use based on public sources
- **Restrictions**: Must display attribution
- **Documentation**: https://developer.seatgeek.com
- **V1 Status**: SECONDARY SOURCE - needs verification

#### Bandsintown API ❌ NOT FEASIBLE FOR V1
- **Capabilities**: Artist-centric only, NOT location-based search
- **Authentication**: Requires artist account or partnership
- **Limitations**: Cannot search ALL concerts by location
- **Documentation**: https://help.artists.bandsintown.com/en/articles/9186477-api-documentation
- **V1 Status**: NOT USABLE - requires artist-specific queries

#### Songkick API ❌ NOT FEASIBLE
- **Status**: NOT accepting new developers
- **Restrictions**: Commercial partnerships only
- **V1 Status**: NOT AVAILABLE

### Dining Agent APIs

#### Google Places API ✅ FREE CREDIT AVAILABLE
- **Current (until Feb 28, 2025)**: $200 monthly credit covers ~11,000 basic searches
- **After March 1, 2025**: Fixed free usage caps per API
- **Capabilities**: Restaurant search by location, ratings, reviews, photos, hours
- **Authentication**: API key required
- **Documentation**: https://developers.google.com/maps/documentation/places
- **V1 Status**: PRIMARY SOURCE

#### Yelp Fusion API ❌ NOT FEASIBLE FOR V1
- **Free Tier**: 30-day trial only (5,000 calls for evaluation)
- **Production Cost**: $229+/month minimum
- **Status**: Transitioned to paid-only in 2024
- **V1 Status**: NOT USABLE - too expensive after trial

#### OpenTable API ❌ NOT FEASIBLE
- **Status**: Partner-only access, not publicly available
- **Requirements**: Must be approved affiliate partner
- **V1 Status**: NOT AVAILABLE

### Events Agent APIs

#### Ticketmaster Discovery API ✅ (Same as Concert Agent)
- **Capabilities**: Sports, arts, theater, family events, comedy
- **Event Filtering**: Can filter by classification (sports, music, arts, etc.)
- **V1 Status**: PRIMARY SOURCE for all event types

#### SeatGeek API ✅ (Same as Concert Agent)
- **Capabilities**: Strong sports coverage, theater, comedy shows
- **Event Filtering**: Can filter by event type
- **V1 Status**: SECONDARY SOURCE for additional coverage

#### AllEvents API ❌ NOT FEASIBLE
- **Cost**: Minimum $500/month, no free tier
- **Requirements**: Business/enterprise focus
- **V1 Status**: NOT USABLE - too expensive

### Locations Agent APIs

#### Google Places API ✅ (Same as Dining Agent)
- **Capabilities**: Attractions, museums, landmarks, points of interest
- **V1 Status**: PRIMARY SOURCE for location data

#### Viator API ❌ NOT FEASIBLE
- **Status**: Partner-only, not publicly available
- **Requirements**: Formal partnership with Viator/Tripadvisor
- **V1 Status**: NOT AVAILABLE

### Web Search Strategy (Critical for V1)
Web search via LangChain tools will fill gaps left by expensive/unavailable APIs. **Prioritized sources** defined for each agent:

**Concert Agent Web Sources** (Priority Order):
1. **Songkick** - Comprehensive concert listings with event detail pages
2. **Bandsintown** - Strong indie/small venue coverage
3. **SeatGeek** - Catches venues not on Ticketmaster (e.g., Tixr-ticketed venues)

**Concert Agent Search Strategy** (Implemented):
- **Day-by-day queries**: Search each date individually for better relevance
- **Dynamic venue discovery**: Auto-discover indie venues per city, then query specifically
- **Multi-domain coverage**: Songkick, Bandsintown, SeatGeek searched in parallel
- **Event page filtering**: Only extract actual event pages (not listing pages)

**Dining Agent Web Sources** (Priority Order):
1. **Reddit** - Local food subreddits (r/food, city-specific)
2. **The Infatuation** - Curated restaurant reviews
3. **OpenTable** - Restaurant availability (web scraping since no API)
4. **Eater** - City-specific restaurant guides

**Events Agent Web Sources** (Priority Order):
1. **Timeout** - Curated city events and guides
2. **Eventbrite** - Local event listings
3. **Google Search** - Queries like "events in {location}" or "things to do this weekend in {location}"
   - Note: Events are highly time-sensitive, search should focus on date ranges

**Locations Agent Web Sources** (Priority Order):
1. **Reddit** - Local city subreddits for authentic recommendations
2. **Timeout** - Curated attractions and activities
3. **Conde Nast Traveler** - High-quality travel recommendations
4. **Travel + Leisure** - Popular attractions and experiences

## Sub-Agent Architecture (V1 - Simplified)

### Web Search Sub-Agent Design Philosophy

**Key Decision: ONE Web Search Sub-Agent per Main Agent**

Each main agent (Concert, Dining, Events, Locations) has a single web search sub-agent that intelligently handles multiple website sources, rather than creating separate sub-agents per website.

**Rationale:**
1. **Simpler Architecture**: 4 main agents with 10 total sub-agents vs 20+ if split by website
2. **LangChain Optimization**: Web search tools designed to query multiple sources efficiently
3. **Intelligent Orchestration**: Sub-agent can prioritize sources, handle failures, batch queries
4. **Cost Efficiency**: Reduces redundant API calls to web search services
5. **Easier Maintenance**: Add/remove sources without restructuring agent hierarchy

**Implementation Pattern:**
```python
# Single Web Search Sub-Agent handles multiple sources
WebSearchSubAgent:
  - Receives: location, date_range, search_context
  - Executes: Multiple site-specific searches in sequence/parallel
  - Returns: Aggregated, deduplicated results from all sources
```

**Example Flow (Dining Web Search Sub-Agent):**
```
Input: "best restaurants in Austin"
  ↓
Search 1: "best restaurants Austin site:reddit.com/r/Austin"
Search 2: "Austin restaurants site:theinfatuation.com"
Search 3: "Austin dining guide site:eater.com"
Search 4: "OpenTable Austin reservations"
  ↓
Parse & aggregate results → Return to Dining Agent
```

**When to Split into Separate Sub-Agents:**
- If a source requires complex scraping (Playwright/Selenium) beyond basic search
- If a source has an actual API (not web search)
- Only split if complexity justifies it (defer to V2)

---

### Concert Agent Sub-Agents

The Concert Agent aggregates ALL concerts in a location/date range (no personalization in v1):

#### 1. Ticketmaster Sub-Agent
- **Purpose**: Primary source for concerts and music events
- **Data Retrieved**: ALL concerts in location/date range
- **Integration**: API key-based REST calls
- **Priority**: PRIMARY - most comprehensive coverage
- **Rate Limit**: 5,000 calls/day

#### 2. SeatGeek Sub-Agent
- **Purpose**: Secondary source for additional coverage
- **Data Retrieved**: Concerts, venues, price ranges
- **Integration**: Client ID authentication (needs verification)
- **Priority**: SECONDARY - if free tier confirmed
- **Attribution**: Must display SeatGeek branding

#### 3. Tavily Web Search Sub-Agent (Enhanced)
- **Purpose**: Comprehensive indie/small venue coverage that Ticketmaster misses
- **Architecture**: Multi-step search with dynamic venue discovery
- **Data Sources**:
  1. Songkick - Event detail pages (`/concerts/`)
  2. Bandsintown - Event detail pages (`/e/`)
  3. SeatGeek - Event pages (`/concert/` or venue-specific URLs)
- **Implementation** (via Tavily API):
  1. **Venue Discovery**: Auto-discover indie venues for location
     - Example: "best indie concert venues San Francisco"
     - Extracts venue names using regex patterns
  2. **Day-by-Day Search**: Query each date individually
     - Example: `"concerts San Francisco January 1 2026 site:songkick.com/concerts"`
  3. **Venue-Specific Search**: Query discovered venues directly
     - Example: `"The Midway San Francisco concerts site:seatgeek.com"`
  4. **Event Page Filtering**: Only keep URLs matching event patterns
  5. **Content Extraction**: Extract full page content for parsing
- **Priority**: CO-PRIMARY - essential for indie venues not on Ticketmaster

**Synthesis Approach**: The Concert Agent will:
1. Query Ticketmaster for all concerts in location/date range (mainstream venues)
2. Run Tavily enhanced search (venue discovery + day-by-day + venue-specific)
3. Extract and parse event pages from Songkick/Bandsintown/SeatGeek
4. Deduplicate events by artist + venue + date
5. Return comprehensive list sorted by date

### Dining Agent Sub-Agents

Given API limitations, the Dining Agent relies heavily on Google Places and web search:

#### 1. Google Places Sub-Agent
- **Purpose**: Primary source for restaurant discovery
- **Data Retrieved**: Restaurant names, ratings, price levels, hours, reviews
- **Integration**: API key authentication
- **Priority**: PRIMARY - $200/month credit currently available
- **Concern**: Pricing changes March 2025

#### 2. Web Search Sub-Agent
- **Purpose**: Curated recommendations and "best of" lists from multiple websites
- **Architecture**: ONE sub-agent that intelligently searches multiple sources
- **Data Sources** (Priority Order):
  1. Reddit - Local food subreddits (r/food, city-specific)
  2. The Infatuation - Curated restaurant reviews
  3. OpenTable - Restaurant availability (web scraping)
  4. Eater - City-specific restaurant guides
- **Implementation**: Sequential or parallel searches across sources
  - Example: `"best restaurants Austin site:reddit.com/r/Austin"`
  - Example: `"Austin dining guide site:eater.com"`
- **Integration**: LangChain web search tools (Tavily, SerpAPI, or DuckDuckGo)
- **Priority**: CO-PRIMARY - essential for quality recommendations

**Synthesis Approach**: The Dining Agent will:
1. Query Google Places for restaurants in area
2. Web search for curated "best restaurants" lists
3. Cross-reference and merge data
4. Rank by ratings, critic recommendations, and recency
5. Return diverse restaurant options

### Events Agent Sub-Agents

The Events Agent covers sports, theater, comedy, and other non-concert events:

#### 1. Ticketmaster Sub-Agent
- **Purpose**: Primary source for ticketed events
- **Data Retrieved**: Sports, arts, theater, family events, comedy
- **Integration**: Same API key as Concert Agent
- **Priority**: PRIMARY - comprehensive coverage
- **Categories**: Can filter by classification

#### 2. SeatGeek Sub-Agent
- **Purpose**: Additional coverage, especially sports
- **Data Retrieved**: Sports events, theater, comedy shows
- **Integration**: Same as Concert Agent (if confirmed)
- **Priority**: SECONDARY - strong sports coverage

#### 3. Web Search Sub-Agent
- **Purpose**: Local and community events not in ticketing systems from multiple websites
- **Architecture**: ONE sub-agent that intelligently searches multiple sources
- **Data Sources** (Priority Order):
  1. Timeout - Curated city events and guides
  2. Eventbrite - Local event listings
  3. Google Search - Queries like "events in {location}" or "things to do this weekend in {location}"
     - **Note**: Events are highly time-sensitive, focus on specific date ranges
- **Implementation**: Time-aware searches across sources
  - Example: `"events Austin December 2024 site:timeout.com"`
  - Example: `"things to do this weekend in Austin"`
- **Integration**: LangChain web search tools (Tavily, SerpAPI, or DuckDuckGo)
- **Priority**: CO-PRIMARY - essential for time-sensitive local events

**Synthesis Approach**: The Events Agent will:
1. Query Ticketmaster for all non-music events
2. Query SeatGeek in parallel (if available)
3. Web search for community events
4. Deduplicate by event name + venue + date
5. Categorize by type (sports, theater, etc.)

### Locations Agent Sub-Agents

The Locations Agent provides attractions, museums, landmarks, and activities:

#### 1. Google Places Sub-Agent
- **Purpose**: Primary source for attractions, landmarks, museums, and POIs
- **Data Retrieved**: Museums, landmarks, historical sites, parks, tours, hours, reviews, photos, coordinates
- **Integration**: API key authentication (same as Dining Agent)
- **Priority**: PRIMARY - comprehensive POI and landmark data
- **Concern**: Same March 2025 pricing change
- **Types Supported**: tourist_attraction, museum, park, art_gallery, landmark, etc.

#### 2. Web Search Sub-Agent
- **Purpose**: Curated attraction lists and hidden gems from multiple websites
- **Architecture**: ONE sub-agent that intelligently searches multiple sources
- **Data Sources** (Priority Order):
  1. Reddit - Local city subreddits for authentic recommendations
  2. Timeout - Curated attractions and activities
  3. Conde Nast Traveler - High-quality travel recommendations
  4. Travel + Leisure - Popular attractions and experiences
- **Implementation**: Curated searches across travel sources
  - Example: `"best things to do Austin site:reddit.com/r/Austin"`
  - Example: `"Austin attractions site:timeout.com"`
- **Integration**: LangChain web search tools (Tavily, SerpAPI, or DuckDuckGo)
- **Priority**: CO-PRIMARY - essential for quality recommendations

**Synthesis Approach**: The Locations Agent will:
1. Query Google Places for museums, landmarks, parks, and attractions in area
2. Web search for curated "best attractions" and "hidden gems" lists
3. Merge and cross-reference data (deduplicating by name/location)
4. Filter by operating hours if time-specific
5. Rank by uniqueness, ratings, and local recommendations
6. Include practical details (hours, admission, accessibility)

### Main Synthesis Agent

The Synthesis Agent aggregates all sub-agent outputs:

**Aggregation Strategy**:
1. **Collect**: Gather all results from main agents
2. **Deduplicate**: Remove duplicates across agents (same venue appearing in concerts and events)
3. **Categorize**: Group by type (concerts, dining, events, attractions)
4. **Rank**: Apply smart ranking based on:
   - User preferences (Spotify data)
   - Temporal relevance (events on specific dates vs. always available)
   - Quality scores (ratings, reviews)
   - Diversity (mix of different types)
5. **Format**: Structure for consumption by various UIs

**Conflict Resolution**:
- If same event from multiple sources: prefer source with more details
- If conflicting times: prefer official source (Ticketmaster > SeatGeek)
- If conflicting prices: show range or lowest available

## Authentication Plan (V1 - Simplified)

### API Key Authentication Only

**V1 eliminates OAuth entirely** - all APIs use simple API key authentication:

#### Ticketmaster Discovery API
- **Auth Method**: API key in query parameter
- **Registration**: developer.ticketmaster.com
- **Storage**: Environment variable or secure config
- **No expiration**: API key remains valid

#### Google Places API
- **Auth Method**: API key in query parameter
- **Registration**: Google Cloud Console
- **Storage**: Environment variable or secure config
- **Billing**: Enable billing account for $200 credit

#### SeatGeek API (if used)
- **Auth Method**: Client ID in query parameter
- **Registration**: developer.seatgeek.com (needs verification)
- **Storage**: Environment variable

### Security Considerations (Simplified)
- Store API keys in environment variables
- Never commit API keys to version control
- Use .env files locally
- Rotate keys if compromised
- All API calls over HTTPS
- Rate limit protection to stay within quotas

### Deferred to V2
- Spotify OAuth for personalized concert recommendations
- User authentication/accounts
- Token refresh mechanisms

## Database Design Evaluation (V1 - Simplified)

### V1 Decision: NO DATABASE

**V1 will NOT use MongoDB or any database.** All queries are real-time with no caching.

**Rationale:**
- Low query volume for personal use (~10-20 queries/day)
- Won't hit API rate limits (5,000/day Ticketmaster)
- Simpler architecture, faster development
- Fresh data more valuable than speed for time-sensitive events
- Can add caching in V2 if needed (not a breaking change)

**V1 Data Flow:**
```
User Query → LangGraph Orchestration → API Calls (real-time) → Synthesis → JSON Output
```

**No persistence layer needed for V1.**

### Caching Strategy for V1

**RECOMMENDATION: Caching is OPTIONAL for v1, add in v2+ if needed**

#### Why Caching is NOT Necessary for V1

1. **Low Query Volume for Personal Use**
   - Ticketmaster: 5,000 calls/day limit
   - Google Places: ~11,000 searches/month with current credit
   - Personal use: 3-4 cities × 10 requests = 40 calls total
   - **Conclusion**: Won't hit rate limits without caching

2. **Time-Sensitive Data Benefits from Real-Time Queries**
   - New concerts/events get added daily
   - Venues sell out
   - Restaurant hours change
   - Fresh data more valuable than speed

3. **Development Speed**
   - Caching adds significant complexity:
     - MongoDB setup and maintenance
     - Cache invalidation logic (hardest problem in CS)
     - TTL management per data type
     - More code to debug and test
   - **v1 Focus**: Get clean data from sources, validate agent orchestration
   - Faster to build and iterate without caching layer

4. **Avoid Premature Optimization**
   - Can always add caching later if needed
   - Better to validate architecture first
   - Real-time queries reveal data quality issues faster

#### When Caching DOES Matter (V2+)

Implement caching when you hit one of these triggers:

1. **Multi-User Production** - Multiple users querying same cities
2. **Scheduled Automation** - Daily/weekly automated runs benefit from caching
3. **API Cost Concerns** - Google Places pricing change (March 2025) may require reducing calls
4. **Web Search Costs** - If LangChain web search has per-query costs
5. **Performance Requirements** - If response time becomes critical

#### Caching Implementation for V2 (Future)

If/when needed, implement selective caching:

**API Response Caching** (24-hour TTL):
- Cache Ticketmaster/Google Places responses
- Reduces repeated queries for same location/date
- Aggressive caching can reduce API calls by 80-90%

**Web Search Caching** (48-72 hour TTL):
- Cache curated content (changes slowly)
- Reddit threads, Eater articles, travel guides
- Reduces web search API costs

**Skip Caching for**:
- Time-sensitive event searches (today/this weekend)
- Real-time availability checks
- User-specific preferences (when v2 adds personalization)

### Pros/Cons Analysis

**Skip Caching in V1 - Pros:**
- ✅ Faster development (30-40% less complexity)
- ✅ Always fresh data
- ✅ No infrastructure overhead
- ✅ Easier debugging
- ✅ Won't hit rate limits with personal use
- ✅ Simpler architecture validation

**Skip Caching in V1 - Cons:**
- ❌ Slower response times (acceptable for v1)
- ❌ More API calls (still well within limits)
- ❌ Can't scale to production without caching (defer to v2)

**Add Caching in V2 - Pros:**
- ✅ Reduces API calls by 80-90%
- ✅ Stays within free tier limits at scale
- ✅ Faster response times
- ✅ Supports scheduled automation
- ✅ MongoDB Atlas free tier available

**Add Caching in V2 - Cons:**
- ❌ Additional infrastructure
- ❌ Potential for stale data
- ❌ Cache invalidation complexity
- ❌ More code to maintain

**Recommendation:** Skip MongoDB entirely for v1, add selective caching in v2 only if needed

## LangChain Integration Assessment

### LangChain Agent Frameworks Research

**LangGraph** (Recommended)
- Low-level orchestration framework
- No hidden prompts or enforced architectures
- Supports diverse control flows
- Production-ready with built-in memory and observability

**Key Capabilities:**
- **Multi-Agent Patterns**: Tool calling, agent supervisor, hierarchical teams
- **Context Engineering**: Fine-grained control over agent inputs
- **Observability**: LangSmith integration for monitoring
- **Flexibility**: Custom workflows without constraints

### Evaluation for Weekenders App

**Fit Assessment:**
- ✅ Perfect for orchestrating multiple specialized agents
- ✅ Tool calling pattern matches our architecture
- ✅ Built-in error handling and retry logic
- ✅ LangSmith provides production observability

**Implementation Approach:**
1. Use supervisor agent pattern
2. Wrap each data agent as a tool
3. Implement custom context for each agent
4. Synthesis agent as final aggregator

### Alternative Orchestration Approaches

**1. Custom Orchestration**
- Pros: Full control, no dependencies
- Cons: Reinventing the wheel, more development time

**2. AutoGen (Microsoft)**
- Pros: Good for conversational agents
- Cons: Less suitable for data aggregation

**3. Direct API Integration**
- Pros: Simpler, fewer dependencies
- Cons: Less flexibility, harder to maintain

**Recommendation:** LangGraph for production, custom for MVP

## Technical Feasibility Analysis (V1 - Rescoped)

### Overall Feasibility Score: 9/10 (Significantly Improved with v1 Simplification)

### Component Risk Assessment

| Component | Feasibility | Risk Level | Critical Issues |
|-----------|------------|------------|-----------------|
| Concert Agent | 9/10 | Low | Ticketmaster confirmed free, SeatGeek needs verification |
| Dining Agent | 8/10 | Low-Medium | Google Places pricing change March 2025 |
| Events Agent | 9/10 | Low | Same APIs as Concert Agent |
| Locations Agent | 8/10 | Low-Medium | Same Google Places pricing concern |
| Synthesis Agent | 9/10 | Low | Straightforward implementation |
| Authentication | 10/10 | None | API keys only, no OAuth |
| Database Layer | 9/10 | Low | Simple caching schema |
| LangChain Integration | 9/10 | Low | Well-suited for orchestration |
| Web Search Integration | 8/10 | Medium | Depends on LangChain web tools |

### Critical Dependencies (V1)
1. **Ticketmaster API** ✅ - FREE tier confirmed: 5,000 calls/day
2. **Google Places API** ⚠️ - FREE credit until Feb 2025, changes after
3. **LangChain/LangGraph** ✅ - Open source, mature
4. **LangChain Web Search Tools** ⚠️ - Need to verify capabilities
5. **SeatGeek API** ⚠️ - Appears free, needs confirmation

**Removed from V1:**
- ❌ MongoDB Atlas - No caching layer needed for v1

### API Cost Analysis for Personal Use

#### Confirmed FREE APIs
- **Ticketmaster Discovery API**: 5,000 calls/day free tier
- **Google Places API**: $200/month credit (until Feb 28, 2025)

#### Likely FREE (Need Verification)
- **SeatGeek API**: Public sources indicate free tier with attribution

#### NOT FEASIBLE for V1
- **Bandsintown API**: Artist-centric, not location-based
- **Songkick API**: Not accepting new developers
- **AllEvents API**: $500+/month minimum
- **OpenTable API**: Partner-only
- **Viator API**: Partner-only
- **Yelp API**: 30-day trial only, $229+/month after

### V1 Advantages Over Original Plan
1. **No OAuth Complexity** - Eliminates entire authentication layer
2. **Confirmed Free APIs** - Ticketmaster verified free
3. **No Database Layer** - Real-time queries only, no MongoDB setup
4. **No Personalization Logic** - Simpler ranking algorithms
5. **Faster Development** - 40-50% less complexity than original plan

## Development Phases (V1 - Simplified Roadmap)

### Phase 1: Core Data Engine - 2-3 weeks
**Goal:** Working prototype with Ticketmaster + Google Places only

**Features:**
- Ticketmaster API integration (concerts + events)
- Google Places API integration (restaurants + attractions)
- Simple LangChain orchestration
- Basic deduplication logic
- JSON output format
- API key authentication only

**Deliverables:**
- Concert Agent (Ticketmaster sub-agent only)
- Events Agent (Ticketmaster sub-agent only)
- Dining Agent (Google Places sub-agent only)
- Locations Agent (Google Places sub-agent only)
- Basic synthesis agent
- CLI or simple REST API interface

**Risk**: Low - all APIs confirmed free

### Phase 2: Web Search Integration - 2-3 weeks
**Goal:** Add web search sub-agents for comprehensive coverage

**Features:**
- LangChain web search tool integration
- Web search sub-agents for all 4 main agents
- Enhanced deduplication across API + web sources
- Improved ranking algorithms

**Deliverables:**
- All agents with web search sub-agents
- Enhanced synthesis with multiple sources
- Deduplication logic across API + web data
- Quality ranking algorithms

**Risk**: Medium - depends on LangChain web search capabilities

### Phase 3: Production Polish - 2-3 weeks
**Goal:** Production-ready system with basic UI

**Features:**
- SeatGeek API integration (if free tier confirmed)
- LangSmith observability
- Rate limiting and quota management
- Choose and implement minimal UI (CLI, web, or email)
- Error handling and retry logic
- Documentation

**Deliverables:**
- Production-ready data engine
- Monitoring and observability
- Basic UI for testing
- API documentation
- Deployment guide

**Risk**: Low - mostly polish and tooling

### Total Timeline: 6-9 weeks (vs 12-18 weeks original)

### Estimated Complexity (V1)

| Phase | Backend Complexity | Integration Complexity | Overall |
|-------|-------------------|----------------------|---------|
| Phase 1 | Low-Medium | Low | Simple |
| Phase 2 | Medium | Medium | Moderate |
| Phase 3 | Low | Low | Simple |

## Open Questions & Recommendations

### Key Architecture Decisions for V1

1. **UI-Agnostic Data Engine**: Backend service that can power any UI
2. **No Personalization**: Geographic discovery only, defer Spotify to v2
3. **Sub-Agent Architecture**: Each main agent orchestrates API + web search
4. **Focus on Confirmed Free APIs**: Ticketmaster + Google Places only in Phase 1
5. **API Key Auth Only**: No OAuth complexity
6. **Aggressive Caching**: Maximize free tier usage
7. **Web Search Critical**: Fill gaps from expensive/unavailable APIs

### Implementation Recommendations Based on API Research

1. **Concert Agent**: Ticketmaster PRIMARY, SeatGeek if verified, web search for local venues
2. **Dining Agent**: Google Places + web search (Eater, Reddit, Infatuation)
3. **Events Agent**: Same as Concert Agent (Ticketmaster/SeatGeek cover all event types)
4. **Locations Agent**: Google Places + web search (Timeout, Atlas Obscura)
5. **Skip Expensive APIs**: Yelp ($229+/month), AllEvents ($500+/month)
6. **Skip Partner-Only APIs**: OpenTable, Viator, Bandsintown (artist-only)
7. **Monitor SeatGeek**: Verify free tier before Phase 3 integration
8. **Plan for Google Changes**: March 2025 pricing shift

### Technical Recommendations (V1)

1. **Phase 1: Ticketmaster + Google Places Only**: Validate architecture before adding complexity
2. **No Caching Layer**: Real-time queries only, skip MongoDB entirely for v1
3. **Use LangGraph**: Perfect for orchestrating sub-agents
4. **Web Search in Phase 2**: After API integration proven
5. **Monitor API Usage**: Track calls to understand actual usage patterns
6. **API Abstraction Layer**: Easy to swap sources if needed
7. **Simple Deduplication**: Hash-based (artist+venue+date) initially
8. **LangSmith from Start**: Observability critical for debugging agents
9. **Defer UI Choice**: Focus on data engine, add UI in Phase 3
10. **JSON Output**: Structured, UI-agnostic format ready for any frontend

### Trade-off Decisions for V1

1. **Data Freshness vs. API Quota**
   - V1 Decision: Real-time queries, no caching
   - Rationale: Won't hit quota with personal use (~10-20 queries/day vs 5,000 limit), fresh data more valuable

2. **Coverage vs. Complexity**
   - V1 Decision: Start with 2 APIs (Ticketmaster + Google), add more later
   - Rationale: Validate architecture before adding sources

3. **Personalization vs. Simplicity**
   - V1 Decision: No personalization, geographic discovery only
   - Rationale: Remove OAuth, faster to build, defer to v2

4. **UI Investment**
   - V1 Decision: Minimal UI (CLI or basic web), focus on data engine
   - Rationale: Architecture validation more important than polish

5. **Web Search Timing**
   - V1 Decision: Phase 2 after API integration proven
   - Rationale: Reduces initial complexity, validates LangChain separately

## Conclusion (V1 - Rescoped)

The Weekenders App V1 is **highly feasible** with a score of **9/10** after API research and v1 simplification. Removing Spotify OAuth and personalization eliminates significant complexity while retaining core value.

### Strengths of V1 Approach:
1. **Confirmed Free APIs**: Ticketmaster verified free (5,000/day), Google Places has $200 credit
2. **No OAuth Complexity**: API keys only, massive simplification
3. **Sub-Agent Architecture**: Proven pattern for multi-source aggregation
4. **UI-Agnostic Design**: Data engine can power any interface
5. **Web Search Integration**: LangChain tools fill gaps from expensive APIs
6. **Faster Timeline**: 6-9 weeks vs 12-18 weeks original

### API Research Summary:

**Confirmed FREE for Personal Use:**
- ✅ **Ticketmaster Discovery API**: 5,000 calls/day, all event types
- ✅ **Google Places API**: $200/month credit (until Feb 28, 2025)

**Likely FREE (Need Verification):**
- ⚠️ **SeatGeek API**: Public sources indicate free tier with attribution

**NOT FEASIBLE (Expensive or Restricted):**
- ❌ **Bandsintown**: Artist-centric only, not location-based
- ❌ **Songkick**: Not accepting new developers
- ❌ **AllEvents**: $500+/month minimum
- ❌ **OpenTable**: Partner-only access
- ❌ **Viator**: Partner-only access
- ❌ **Yelp**: 30-day trial only, then $229+/month

### Recommended Sub-Agent Architecture:

**Concert Agent:**
- Ticketmaster Sub-Agent (PRIMARY)
- SeatGeek Sub-Agent (SECONDARY, if verified)
- Web Search Sub-Agent (local venues)

**Dining Agent:**
- Google Places Sub-Agent (PRIMARY)
- Web Search Sub-Agent (Eater, Reddit, Infatuation)

**Events Agent:**
- Ticketmaster Sub-Agent (PRIMARY, all non-music events)
- SeatGeek Sub-Agent (SECONDARY, sports focus)
- Web Search Sub-Agent (Eventbrite, community events)

**Locations Agent:**
- Google Places Sub-Agent (PRIMARY, attractions/museums)
- Web Search Sub-Agent (Timeout, Atlas Obscura)

### Critical Findings:

1. **Bandsintown NOT Usable**: API is artist-centric, cannot search ALL concerts by location
2. **Most Tour/Dining APIs Partner-Only**: Viator, OpenTable require business partnerships
3. **Yelp Too Expensive**: $229+/month after 30-day trial
4. **Google Places Pricing Change**: March 2025 shift from credit to usage caps - monitor closely
5. **SeatGeek Needs Verification**: Cannot confirm free tier access via official docs

### How Removing Spotify OAuth Simplifies V1:

1. **No Authentication Layer**: Eliminates OAuth flows, token refresh, secure storage
2. **No User Accounts**: Simpler database (caching only, no user tables)
3. **No Personalization Logic**: Simpler ranking (by date/rating vs. user preferences)
4. **No Artist Matching**: Don't need to cross-reference Spotify artists with concert APIs
5. **Faster Development**: 30-40% less code, fewer dependencies
6. **Easier Testing**: No OAuth mocking, simpler integration tests
7. **Lower Maintenance**: Fewer APIs to monitor, no token expiration issues

### V1 Success Factors:
- Aggressive caching to stay within Ticketmaster 5,000/day limit
- Effective web search integration for quality recommendations
- MongoDB Atlas free tier for caching
- LangGraph for clean sub-agent orchestration
- Monitor Google Places pricing (March 2025)
- Verify SeatGeek free tier before integration

### Recommended Implementation Path:
1. **Phase 1 (2-3 weeks)**: Core engine with Ticketmaster + Google Places APIs only
2. **Phase 2 (2-3 weeks)**: Add web search sub-agents for all main agents
3. **Phase 3 (2-3 weeks)**: Production polish, observability, basic UI

**Total: 6-9 weeks to production-ready v1**

The project should proceed immediately with Phase 1, focusing on architecture validation using confirmed free APIs. V2 can add personalization (Spotify) and additional data sources once the core engine is proven.