"""
Concert Agent - Main Orchestrator
==================================

Orchestrates concert discovery using modular tools.

Architecture:
- Context Router: Determines search parameters (radius, coordinates, strategy)
- Ticketmaster Tool: Fetches structured concert data from Ticketmaster API
- Tavily Tool: Extracts indie/small venue concerts from web sources
- Aggregation Tool: Parses, deduplicates, and formats all results

Each tool operates independently for:
- LangSmith tracing (separate runs per tool)
- Modularity (tools in isolation)
- Testability (unit test each tool)
- Reusability (other agents can import tools)
"""

import sys
import os
import json

# Add parent directory to import context_router
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from context_router import analyze_city

# Import modular tools
from tools import (
    get_concerts_ticketmaster,
    get_concerts_tavily_enhanced,
    aggregate_concerts
)
from schemas import ConcertResults


def run_concert_agent(
    location: str,
    start_date: str,
    end_date: str
) -> ConcertResults:
    """
    Main Concert Agent - orchestrates all tools.

    CONTEXT-DRIVEN: All search parameters come from Context Router.

    Args:
        location: User's location input (e.g., "Austin", "NYC")
        start_date: ISO date (YYYY-MM-DD)
        end_date: ISO date (YYYY-MM-DD)

    Returns:
        ConcertResults with all concerts found

    Flow:
        1. Context Router → Analyzes location, sets search parameters
        2. Ticketmaster Tool → Fetches structured concert data
        3. Tavily Tool → Extracts indie/small venue concerts from web
        4. Aggregation Tool → Parses web pages, deduplicates, formats
        5. Return structured results

    Example:
        >>> results = run_concert_agent("Austin, TX", "2025-01-10", "2025-01-17")
        >>> results.total_count
        45
        >>> results.concerts[0].name
        "Billy Strings"
    """

    print("\n" + "="*70)
    print("🎸 CONCERT AGENT")
    print("="*70)

    # Step 1: Get context from Context Router
    print(f"\n1️⃣  Getting search context for '{location}'...")
    context = analyze_city(location, start_date, end_date)

    print(f"   ✅ Context: {context.area_classification}")
    print(f"   📍 Searching: {context.location_info.normalized_location}")
    print(f"   📏 Radius: {context.search_parameters.concert_radius_miles} miles (from context)")
    print(f"   🗺️  Center: {context.location_info.latitude}, {context.location_info.longitude}")

    # Step 2: Query Ticketmaster (mainstream/big venues)
    print(f"\n2️⃣  Querying Ticketmaster API...")
    ticketmaster_results = get_concerts_ticketmaster(context, start_date, end_date)

    # Step 3: Query Tavily SEARCH → EXTRACT (indie/small venues)
    print(f"\n3️⃣  Querying Tavily for indie/small venue concerts...")
    web_page_contents = get_concerts_tavily_enhanced(context, start_date, end_date)

    # Step 4: Aggregate with Claude Haiku
    print(f"\n4️⃣  Aggregating results with Claude Haiku...")
    final_results = aggregate_concerts(
        ticketmaster_results,
        web_page_contents,
        context,
        start_date,
        end_date
    )

    # Summary
    print("\n" + "="*70)
    print("✅ CONCERT AGENT COMPLETE")
    print("="*70)
    print(f"\n📊 Results Summary:")
    print(f"   Total Concerts: {final_results.total_count}")
    print(f"   Date Range: {final_results.date_range}")
    print(f"   Location: {final_results.search_location}")
    print(f"   Search Radius: {final_results.search_radius_miles} miles")

    # Show breakdown by source
    ticketmaster_count = sum(1 for c in final_results.concerts if c.source == "ticketmaster")
    web_count = sum(1 for c in final_results.concerts if c.source == "web")
    print(f"\n   Sources:")
    print(f"     • Ticketmaster: {ticketmaster_count} concerts")
    print(f"     • Web (indie/small venues): {web_count} concerts")

    if final_results.concerts:
        print(f"\n🎵 Sample Concerts:")
        for i, concert in enumerate(final_results.concerts[:8], 1):
            print(f"   {i}. {concert.name}")
            print(f"      📍 {concert.venue} ({concert.location})")
            print(f"      📅 {concert.date} {concert.time or ''}")
            if concert.price_range:
                print(f"      💰 {concert.price_range}")
            print(f"      🔗 Source: {concert.source}")

    print("\n" + "="*70 + "\n")

    return final_results


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    """Test the Concert Agent with future dates"""

    print("\n🧪 TESTING CONCERT AGENT (Modular Architecture)\n")
    print("Components:")
    print("  • Context Router (determines search parameters)")
    print("  • Ticketmaster Tool (big venues)")
    print("  • Tavily Tool (indie/small venues via SEARCH → EXTRACT)")
    print("  • Aggregation Tool (Claude parsing & deduplication)")
    print("\nEach tool traces separately in LangSmith!\n")

    # Test with Austin (medium city, great music scene)
    print("="*70)
    print("TEST: Austin, Texas (Known for live music, small venues)")
    print("="*70)

    results_austin = run_concert_agent(
        "Austin, Texas",
        "2025-01-10",
        "2025-01-17"
    )

    # Save results to file
    output_file = "concert_results_austin_modular.json"
    with open(output_file, "w") as f:
        json.dump(results_austin.model_dump(), f, indent=2)
    print(f"\n💾 Results saved to: {output_file}")

    print("\n" + "="*70)
    print("COST ESTIMATE")
    print("="*70)
    print(f"\n💰 Per location query:")
    print(f"   • Context Router (Haiku): $0.0003")
    print(f"   • Ticketmaster Tool: Free")
    print(f"   • Tavily Tool (SEARCH): Free")
    print(f"   • Tavily Tool (EXTRACT ~10 pages): $0.01")
    print(f"   • Aggregation Tool (Haiku): $0.001")
    print(f"   TOTAL: ~$0.011 per location")
    print(f"\n✅ Modular architecture ready for LangSmith tracing!")
