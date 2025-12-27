"""
Concert Agent Test Runner
==========================

Organized test framework that saves results by:
- Location (e.g., Austin_TX, New_York_NY)
- Date range (e.g., 2025-01-10_to_2025-01-17)
- Data source (ticketmaster_results.json, tavily_results.json, final_results.json)

This allows tracking results over time and comparing different sources.

Directory Structure:
test_results/
├── Austin_TX/
│   └── 2025-01-10_to_2025-01-17/
│       ├── ticketmaster_results.json
│       ├── tavily_results.json
│       ├── final_results.json
│       └── metadata.json
├── New_York_NY/
│   └── 2025-01-15_to_2025-01-22/
│       ├── ticketmaster_results.json
│       ├── tavily_results.json
│       ├── final_results.json
│       └── metadata.json
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

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
from date_utils import get_concert_weekend_dates


def sanitize_location_name(location: str) -> str:
    """Convert location to filesystem-safe folder name"""
    # Replace spaces and commas with underscores
    safe_name = location.replace(", ", "_").replace(" ", "_").replace(",", "")
    return safe_name


def create_test_directories(location: str, start_date: str, end_date: str) -> Path:
    """
    Create directory structure for test results.

    Returns:
        Path to the test run directory
    """
    base_dir = Path(__file__).parent / "test_results"
    location_dir = base_dir / sanitize_location_name(location)
    date_dir = location_dir / f"{start_date}_to_{end_date}"

    date_dir.mkdir(parents=True, exist_ok=True)

    return date_dir


def save_test_results(
    output_dir: Path,
    ticketmaster_results: list,
    tavily_pages: list,
    final_results: ConcertResults,
    context,
    start_date: str,
    end_date: str,
    execution_time: float
):
    """
    Save all test results to organized directory structure.

    Saves:
    - ticketmaster_results.json (raw Ticketmaster data)
    - tavily_results.json (raw web page contents)
    - final_results.json (aggregated concert list)
    - metadata.json (test run info)
    """

    # Save Ticketmaster results
    with open(output_dir / "ticketmaster_results.json", "w") as f:
        json.dump({
            "source": "ticketmaster",
            "count": len(ticketmaster_results),
            "results": ticketmaster_results
        }, f, indent=2)

    # Save Tavily results (web pages)
    with open(output_dir / "tavily_results.json", "w") as f:
        json.dump({
            "source": "tavily_web_extraction",
            "page_count": len(tavily_pages),
            "pages": [
                {
                    "page_number": i + 1,
                    "content_preview": page[:500] + "..." if len(page) > 500 else page,
                    "content_length": len(page)
                }
                for i, page in enumerate(tavily_pages)
            ]
        }, f, indent=2)

    # Save final aggregated results
    with open(output_dir / "final_results.json", "w") as f:
        json.dump(final_results.model_dump(), f, indent=2)

    # Save metadata
    with open(output_dir / "metadata.json", "w") as f:
        json.dump({
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "location": context.location_info.normalized_location,
                "date_range": f"{start_date} to {end_date}",
                "execution_time_seconds": round(execution_time, 2)
            },
            "context": {
                "area_classification": context.area_classification,
                "city_type": context.city_type,
                "search_radius_miles": context.search_parameters.concert_radius_miles,
                "coordinates": {
                    "lat": context.location_info.latitude,
                    "lon": context.location_info.longitude
                }
            },
            "results_summary": {
                "total_concerts": final_results.total_count,
                "ticketmaster_count": len(ticketmaster_results),
                "web_pages_parsed": len(tavily_pages),
                "source_breakdown": {
                    "ticketmaster": sum(1 for c in final_results.concerts if c.source == "ticketmaster"),
                    "web": sum(1 for c in final_results.concerts if c.source == "web")
                }
            }
        }, f, indent=2)

    print(f"\n💾 Results saved to: {output_dir}")
    print(f"   • ticketmaster_results.json ({len(ticketmaster_results)} concerts)")
    print(f"   • tavily_results.json ({len(tavily_pages)} pages)")
    print(f"   • final_results.json ({final_results.total_count} concerts)")
    print(f"   • metadata.json")


def test_concert_agent(location: str, start_date: str, end_date: str):
    """
    Run Concert Agent test with organized result saving.

    Args:
        location: City name (e.g., "Austin, Texas")
        start_date: ISO date (YYYY-MM-DD)
        end_date: ISO date (YYYY-MM-DD)
    """

    print("\n" + "="*70)
    print(f"🎸 TESTING CONCERT AGENT: {location}")
    print("="*70)

    start_time = datetime.now()

    # Create output directory
    output_dir = create_test_directories(location, start_date, end_date)
    print(f"\n📁 Output directory: {output_dir}")

    # Step 1: Context Router
    print(f"\n1️⃣  Getting search context for '{location}'...")
    context = analyze_city(location, start_date, end_date)

    print(f"   ✅ Context: {context.area_classification}")
    print(f"   📍 Searching: {context.location_info.normalized_location}")
    print(f"   📏 Radius: {context.search_parameters.concert_radius_miles} miles")

    # Step 2: Ticketmaster Tool
    print(f"\n2️⃣  Ticketmaster Tool...")
    ticketmaster_results = get_concerts_ticketmaster(context, start_date, end_date)

    # Step 3: Tavily Tool
    print(f"\n3️⃣  Tavily Tool (SEARCH → EXTRACT)...")
    tavily_pages = get_concerts_tavily_enhanced(context, start_date, end_date)

    # Step 4: Aggregation Tool
    print(f"\n4️⃣  Aggregation Tool...")
    final_results = aggregate_concerts(
        ticketmaster_results,
        tavily_pages,
        context,
        start_date,
        end_date
    )

    # Calculate execution time
    execution_time = (datetime.now() - start_time).total_seconds()

    # Save results
    save_test_results(
        output_dir,
        ticketmaster_results,
        tavily_pages,
        final_results,
        context,
        start_date,
        end_date,
        execution_time
    )

    # Summary
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)
    print(f"\n📊 Summary:")
    print(f"   Location: {context.location_info.normalized_location}")
    print(f"   Total Concerts: {final_results.total_count}")
    print(f"   Ticketmaster: {len(ticketmaster_results)} concerts")
    print(f"   Web Pages Parsed: {len(tavily_pages)} pages")
    print(f"   Execution Time: {execution_time:.2f}s")

    # Source breakdown
    tm_count = sum(1 for c in final_results.concerts if c.source == "ticketmaster")
    web_count = sum(1 for c in final_results.concerts if c.source == "web")
    print(f"\n   Final Results Breakdown:")
    print(f"     • From Ticketmaster: {tm_count}")
    print(f"     • From Web: {web_count}")

    # Sample concerts
    if final_results.concerts:
        print(f"\n🎵 Sample Concerts (first 5):")
        for i, concert in enumerate(final_results.concerts[:5], 1):
            print(f"   {i}. {concert.name}")
            print(f"      {concert.venue} - {concert.date}")
            print(f"      Source: {concert.source}")

    print("\n" + "="*70 + "\n")

    return final_results


def run_concert_agent(location: str, weekend: str = "next"):
    """
    Run the concert agent for a location using automatic weekend date calculation.

    Args:
        location: City name (e.g., "Austin, Texas", "New York, NY")
        weekend: "next" for next weekend, "this" for current weekend

    Returns:
        ConcertResults object with all discovered concerts
    """
    start_date, end_date = get_concert_weekend_dates(weekend)
    return test_concert_agent(location, start_date, end_date)


if __name__ == "__main__":
    """
    Run tests for multiple locations to validate:
    - Modular architecture works
    - Each tool operates independently
    - Results are properly organized
    - Small venues are captured

    Uses automatic date calculation: Thu-Sat of next weekend
    """

    # Get next weekend dates (Thu-Sat)
    start_date, end_date = get_concert_weekend_dates("next")

    print("\n" + "="*70)
    print("🧪 CONCERT AGENT TEST SUITE")
    print("="*70)
    print("\nModular Architecture:")
    print("  ✓ Context Router (determines parameters)")
    print("  ✓ Ticketmaster Tool (big venues)")
    print("  ✓ Tavily Tool (indie/small venues)")
    print("  ✓ Aggregation Tool (parsing & dedup)")
    print(f"\n📅 Date Range: {start_date} to {end_date} (Thu-Sat)")
    print("Results saved to: test_results/[Location]/[Date_Range]/")
    print("="*70)

    # Test 1: Austin (medium city, great music scene, lots of small venues)
    test_concert_agent(
        location="Austin, Texas",
        start_date=start_date,
        end_date=end_date
    )

    # Test 2: Palo Alto (small area, should expand search)
    test_concert_agent(
        location="Palo Alto, CA",
        start_date=start_date,
        end_date=end_date
    )

    # Test 3: Nashville (another music city)
    test_concert_agent(
        location="Nashville, Tennessee",
        start_date=start_date,
        end_date=end_date
    )

    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETE")
    print("="*70)
    print("\n📁 Check test_results/ directory for organized output")
    print("   Each location has separate folders by date range")
    print("   Each test run includes:")
    print("     • ticketmaster_results.json (raw Ticketmaster data)")
    print("     • tavily_results.json (web pages extracted)")
    print("     • final_results.json (aggregated concert list)")
    print("     • metadata.json (test run details)")
    print("\n💰 Estimated cost: ~$0.033 (3 locations × $0.011)")
    print("="*70 + "\n")
