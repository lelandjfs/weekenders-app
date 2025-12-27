"""
Neighborhood Discovery Tool
============================

Discovers trendy/foodie neighborhoods in a city using web search.
Uses Claude Haiku to extract neighborhood names from search results.
"""

import requests
import json
from typing import List, Set

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    TAVILY_API_KEY,
    ANTHROPIC_API_KEY,
    MAX_NEIGHBORHOODS
)
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate


def discover_neighborhoods(city: str, max_neighborhoods: int = None) -> List[str]:
    """
    Discover trendy/foodie neighborhoods for a city.

    Uses web search (especially Reddit) to find neighborhoods known for good food,
    then uses Claude Haiku to extract neighborhood names.

    Args:
        city: City name (e.g., "San Francisco", "Austin")
        max_neighborhoods: Maximum neighborhoods to return (default: 5)

    Returns:
        List of neighborhood names
    """
    if max_neighborhoods is None:
        max_neighborhoods = MAX_NEIGHBORHOODS

    print(f"   → Discovering neighborhoods for {city}...")

    # Search queries - prioritize Reddit for authentic local recommendations
    queries = [
        f"best food neighborhoods {city} site:reddit.com",
        f"trendy neighborhoods {city} site:reddit.com",
        f"foodie neighborhoods {city}",
        f"best neighborhoods to eat {city}",
    ]

    all_content = []

    for query in queries:
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                headers={"Content-Type": "application/json"},
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "max_results": 5,
                    "search_depth": "basic"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            for result in data.get("results", []):
                text = f"{result.get('title', '')} {result.get('content', '')}"
                all_content.append(text)

        except Exception as e:
            print(f"   ⚠️ Query failed: {e}")
            continue

    if not all_content:
        print(f"   ⚠️ No search results, will search city-wide")
        return []

    # Use Claude Haiku to extract neighborhoods
    neighborhoods = _extract_with_haiku(all_content, city, max_neighborhoods)

    if neighborhoods:
        print(f"   ✅ Found {len(neighborhoods)} neighborhoods: {', '.join(neighborhoods)}")
    else:
        print(f"   ⚠️ No neighborhoods found, will search city-wide")

    return neighborhoods


def _extract_with_haiku(
    search_results: List[str],
    city: str,
    max_neighborhoods: int
) -> List[str]:
    """
    Use Claude Haiku to extract neighborhood names from search results.
    """
    llm = ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        anthropic_api_key=ANTHROPIC_API_KEY,
        temperature=0,
        max_tokens=1000
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a neighborhood extraction engine. Extract ONLY actual neighborhood names from the search results.

Rules:
1. Only extract real neighborhood names in {city}
2. Do NOT include generic words like "Property", "Screening", "Bakeries", "Restaurant", etc.
3. Do NOT include city names, state names, or country names
4. Focus on neighborhoods known for good food/dining
5. Return the top {max_neighborhoods} most frequently mentioned neighborhoods

OUTPUT FORMAT - Return ONLY valid JSON:
{{"neighborhoods": ["Neighborhood1", "Neighborhood2", "Neighborhood3"]}}"""),
        ("human", """Extract neighborhood names from these search results about food areas in {city}:

{content}

Return neighborhoods as JSON.""")
    ])

    chain = prompt | llm

    try:
        # Combine and truncate content
        combined = "\n\n".join(search_results)
        if len(combined) > 8000:
            combined = combined[:8000]

        response = chain.invoke({
            "content": combined,
            "city": city,
            "max_neighborhoods": max_neighborhoods
        })

        content = response.content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        # Find JSON in response
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            content = content[json_start:json_end]

        # Parse JSON
        data = json.loads(content)
        neighborhoods = data.get("neighborhoods", [])

        # Limit to max
        return neighborhoods[:max_neighborhoods]

    except Exception as e:
        print(f"   ⚠️ Haiku extraction error: {e}")
        print(f"   → Raw response: {response.content if 'response' in dir() else 'N/A'}")
        return []
