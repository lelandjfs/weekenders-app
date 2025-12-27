"""
Debug script to see what neighborhood discovery is finding.
"""

import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import TAVILY_API_KEY

def debug_search(city: str):
    """See raw search results for neighborhood queries."""

    queries = [
        f"best food neighborhoods {city} site:reddit.com",
        f"trendy neighborhoods {city} site:reddit.com",
        f"where to eat neighborhoods {city}",
        f"foodie neighborhoods {city}",
    ]

    print(f"\n{'='*60}")
    print(f"DEBUG: Neighborhood search for {city}")
    print(f"{'='*60}\n")

    for query in queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 50)

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

            for i, result in enumerate(data.get("results", []), 1):
                title = result.get("title", "")
                url = result.get("url", "")
                content = result.get("content", "")[:300]

                print(f"\n{i}. {title}")
                print(f"   URL: {url}")
                print(f"   Content: {content}...")

        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    city = sys.argv[1] if len(sys.argv) > 1 else "San Francisco"
    debug_search(city)
