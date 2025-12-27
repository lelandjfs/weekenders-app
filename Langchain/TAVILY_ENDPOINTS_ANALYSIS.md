# Tavily API Endpoints Analysis for All Agents

## Problem Statement

We're building 4 agents (Concert, Dining, Events, Locations) that need web data. Tavily has 3 endpoints - which one should each agent use?

**Current Issue:** Concert Agent using SEARCH returns garbage like:
- "Live music in Austin on December 15th, 2024 - Do512" ❌
- "venue": "See details" ❌
- "date": "See details" ❌

These are **listing page titles**, not actual concert data.

---

## Three Tavily Endpoints - Complete Spec

### 1. SEARCH Endpoint (General Web Search)

**What it does:** Google-like search, returns page titles + snippets

**Request:**
```json
{
  "api_key": "your_key",
  "query": "concerts in Austin Dec 6-15",

  // Optional parameters:
  "max_results": 10,              // 0-20, default: 5
  "search_depth": "basic",        // "basic" or "advanced"
  "include_domains": [],          // Only search these domains
  "exclude_domains": [],          // Exclude these domains
  "include_raw_content": false,   // Get full page content (expensive)
  "chunks_per_source": 3,         // How many content chunks per result
  "topic": "general",             // "general", "news", "finance"
  "time_range": "month"           // "day", "week", "month", "year"
}
```

**Response:**
```json
{
  "query": "concerts in Austin Dec 6-15",
  "answer": "AI-generated summary of search results",
  "results": [
    {
      "title": "Live music in Austin - Do512",
      "url": "https://do512.com/events/...",
      "content": "Check out live music happening in Austin this week. Over 100 shows...",
      "score": 0.85,
      "favicon": "https://do512.com/favicon.ico",
      "raw_content": null  // Only if include_raw_content=true
    }
  ],
  "images": [],
  "response_time": 1.67,
  "request_id": "abc123"
}
```

**What You Get:**
- ✅ Page titles (200 chars)
- ✅ Content snippets (200-300 chars per chunk)
- ✅ Relevance scores
- ❌ NOT full page content (unless include_raw_content=true, expensive)
- ❌ NOT structured data

**Cost:** Included in free tier (1,000 searches/month free)

---

### 2. EXTRACT Endpoint (Pull Full Content from Known URLs)

**What it does:** You provide URLs, it extracts ALL content from those pages

**Request:**
```json
{
  "urls": [
    "https://vividseats.com/austin-concerts",
    "https://eater.com/austin-restaurants-guide"
  ],

  // Optional:
  "include_images": false,
  "include_favicon": false,
  "extract_depth": "basic",      // "basic" or "advanced"
  "format": "markdown",           // "markdown" or "text"
  "timeout": 30                   // 1-60 seconds
}
```

**Response:**
```json
{
  "results": [
    {
      "url": "https://vividseats.com/austin-concerts",
      "raw_content": "[FULL PAGE CONTENT - could be 5000+ words, all text extracted]",
      "images": [],
      "favicon": "https://vividseats.com/favicon.ico"
    }
  ],
  "failed_results": [],
  "response_time": 2.3,
  "request_id": "xyz789"
}
```

**What You Get:**
- ✅ FULL page text content (thousands of words)
- ✅ Structured in markdown or plain text
- ✅ All text from the page
- ❌ Still need to parse/extract specific data
- ❌ Need to know URLs in advance

**Cost:** $1 per 1,000 extractions (after free tier)

**When to Use:** When you have specific URLs and need their full content

---

### 3. CRAWL Endpoint (Website Traversal) - BETA

**What it does:** Crawls entire website, follows links, extracts content from many pages

**Request:**
```json
{
  "url": "vividseats.com",
  "instructions": "Find all concerts in Austin, Texas between Dec 6-15, 2024",

  // Optional:
  "max_depth": 2,                 // 1-5, how many link levels deep
  "max_breadth": 20,              // Pages per level
  "limit": 50,                    // Total results returned
  "select_paths": ["/austin", "/concerts"],
  "exclude_paths": ["/account", "/cart"],
  "select_domains": ["vividseats.com"],
  "exclude_domains": [],
  "allow_external": true,
  "include_images": false,
  "extract_depth": "basic",
  "format": "markdown",
  "timeout": 150                  // 10-150 seconds
}
```

**Response:**
```json
{
  "base_url": "vividseats.com",
  "results": [
    {
      "url": "vividseats.com/austin-concerts/billy-strings",
      "raw_content": "[Full page content for Billy Strings concert]"
    },
    {
      "url": "vividseats.com/austin-concerts/taylor-swift",
      "raw_content": "[Full page content for Taylor Swift concert]"
    }
    // ... up to 50 pages
  ],
  "response_time": 45.2,
  "request_id": "def456"
}
```

**What You Get:**
- ✅ Multiple pages from website
- ✅ Full content from each page
- ✅ Follows links automatically
- ❌ EXPENSIVE (processes many pages)
- ❌ Slow (can take 30-150 seconds)
- ⚠️ Beta status (may have issues)

**Cost:** $5 per 1,000 pages crawled

**When to Use:** When you need to traverse entire sections of a website

---

## Agent-Specific Recommendations

### 🎸 CONCERT AGENT: **Drop Tavily Entirely**

**Problem:**
- Web search returns listing pages ("Do512", "Bandsintown"), not concerts
- Even with full content, parsing concert details is unreliable
- Ticketmaster API already gives us 90%+ of concerts

**Recommendation:** ❌ **Remove Tavily from Concert Agent**

**New Flow:**
```
1. Context Router → coordinates + radius
2. Ticketmaster API → structured concert data
3. [Future] SeatGeek API → additional concerts
4. Claude Aggregation → deduplicate
```

**Why:**
- ✅ Ticketmaster has clean, structured data
- ✅ No parsing errors
- ✅ Cheaper (one less API call)
- ✅ Faster execution

**What we lose:**
- Very small local concerts not on Ticketmaster (rare, and usually no structured data anyway)

---

### 🍽️ DINING AGENT: **Use SEARCH with `include_domains`**

**Why it works:**
- Restaurant reviews have names/descriptions in snippets
- Eater, Infatuation write detailed content
- Reddit threads have recommendations

**Recommended Implementation:**
```python
{
  "query": f"best restaurants {location}",
  "include_domains": [
    "eater.com",
    "theinfatuation.com",
    "reddit.com",
    "opentable.com"
  ],
  "search_depth": "advanced",
  "max_results": 15,
  "chunks_per_source": 3  // Get more content per source
}
```

**What You'll Get:**
```json
{
  "title": "The 18 Best Restaurants in Austin Right Now",
  "url": "https://eater.com/austin/...",
  "content": "1. Uchi - Contemporary Japanese with exceptional sushi. 2. Franklin Barbecue - Legendary Texas BBQ worth the wait. 3. Loro - Asian smokehouse fusion..."
}
```

✅ **Restaurant names in content**
✅ **Descriptions in snippets**
✅ **Good for Claude to parse**

**Alternative (if snippets insufficient):**
Use SEARCH → EXTRACT two-step:
1. Search for "best restaurants Austin"
2. Extract full content from top 3-5 URLs
3. Claude parses full articles

---

### 🎭 EVENTS AGENT: **Use SEARCH with `include_domains`**

**Why it works:**
- Event listings have names/dates in titles
- Timeout, Eventbrite write good descriptions
- Better for non-ticketed events (festivals, markets, etc.)

**Recommended Implementation:**
```python
{
  "query": f"events {location} {date_range}",
  "include_domains": [
    "timeout.com",
    "eventbrite.com",
    "facebook.com/events"  // If accessible
  ],
  "search_depth": "advanced",
  "max_results": 20,
  "time_range": "month"  // Only recent results
}
```

**What You'll Get:**
```json
{
  "title": "The 20 Best Things to Do in Austin This Weekend",
  "content": "1. Austin Food + Wine Festival (Dec 6-8) - Three days of tastings. 2. South Congress Holiday Market (Dec 7) - Local artisans and vendors..."
}
```

✅ **Event names in snippets**
✅ **Dates often included**
✅ **Descriptions available**

---

### 🗺️ LOCATIONS AGENT: **Use SEARCH with `include_domains`**

**Why it works:**
- Attraction guides have names/descriptions
- Travel sites write detailed content
- Reddit has authentic local recommendations

**Recommended Implementation:**
```python
{
  "query": f"best things to do {location} attractions museums",
  "include_domains": [
    "timeout.com",
    "reddit.com",
    "cntraveler.com",      // Conde Nast Traveler
    "travelandleisure.com",
    "atlasobscura.com"     // Unique/hidden gems
  ],
  "search_depth": "advanced",
  "max_results": 15,
  "chunks_per_source": 3
}
```

**What You'll Get:**
```json
{
  "title": "15 Best Things to Do in Austin",
  "content": "1. Barton Springs Pool - Natural spring-fed pool in Zilker Park. 2. Texas State Capitol - Free tours of stunning government building. 3. LBJ Presidential Library..."
}
```

✅ **Attraction names in content**
✅ **Good descriptions**
✅ **Location details**

---

## Key Parameters for Success

### For All Agents Using SEARCH:

**1. Use `include_domains`** - Target quality sources
```python
"include_domains": ["eater.com", "timeout.com", "reddit.com"]
```

**2. Use `search_depth: "advanced"`** - Better results
```python
"search_depth": "advanced"  # More thorough than "basic"
```

**3. Increase `chunks_per_source`** - More content per result
```python
"chunks_per_source": 3  # Default is 1, get more context
```

**4. Increase `max_results`** - More options for Claude
```python
"max_results": 15-20  # More results = better aggregation
```

---

## When to Use Each Endpoint

| Endpoint | Use When | Cost | Concert | Dining | Events | Locations |
|----------|----------|------|---------|--------|--------|-----------|
| **SEARCH** | Need snippets from many sources | Free (1K/mo) | ❌ | ✅ | ✅ | ✅ |
| **EXTRACT** | Have specific URLs, need full content | $1/1K | ❌ | 🟡 | 🟡 | 🟡 |
| **CRAWL** | Need to traverse whole site | $5/1K pages | ❌ | ❌ | ❌ | ❌ |

🟡 = Optional two-step approach (SEARCH → EXTRACT) if snippets insufficient

---

## Cost Analysis

### Current Approach (All Agents Use SEARCH):
- Concert: $0 (Tavily free) + $0.0003 (Claude) = **Drop Tavily!**
- Dining: $0 (Tavily free) + $0.0003 (Claude) = **$0.0003**
- Events: $0 (Tavily free) + $0.0003 (Claude) = **$0.0003**
- Locations: $0 (Tavily free) + $0.0003 (Claude) = **$0.0003**

**Total per location query: ~$0.0009** (all 4 agents, with Concert using Ticketmaster only)

### If Using SEARCH → EXTRACT (two-step):
- Dining: $0 (SEARCH) + $0.003 (3 EXTRACTs) + $0.0003 (Claude) = **$0.0033**
- Would increase to **~$0.01 per location query**

**Recommendation:** Stick with SEARCH for now, only add EXTRACT if data quality insufficient

---

## Implementation Summary

### ✅ Final Approach:

**Concert Agent:**
- Remove Tavily completely
- Ticketmaster API only (clean structured data)
- Future: Add SeatGeek API

**Dining Agent:**
- Tavily SEARCH with `include_domains` (Eater, Infatuation, Reddit, OpenTable)
- `search_depth: "advanced"`
- `chunks_per_source: 3`

**Events Agent:**
- Tavily SEARCH with `include_domains` (Timeout, Eventbrite)
- Focus on non-ticketed events (Ticketmaster handles ticketed)

**Locations Agent:**
- Tavily SEARCH with `include_domains` (Timeout, Reddit, travel sites)
- Good for attractions, museums, landmarks

**All use Claude Haiku for aggregation** (~$0.0003 each)

---

## Next Steps

1. ✅ Remove Tavily from Concert Agent
2. ✅ Update Dining/Events/Locations agents to use `include_domains`
3. Test data quality with refined web search parameters
4. Add EXTRACT as fallback if needed (phase 2)
