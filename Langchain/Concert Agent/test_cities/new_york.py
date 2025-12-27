"""
New York Concert Test
=====================

Test Concert Agent for NYC to verify:
- Songkick event pages are working
- Brooklyn/Queens concerts are captured
- Large metro neighborhood strategy works
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to import context_router
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from context_router import analyze_city

# Import modular tools
from tools import (
    get_concerts_ticketmaster,
    get_concerts_tavily_enhanced,
    aggregate_concerts
)

def test_new_york():
    """Test NYC concerts - should catch Brooklyn, Queens, etc."""

    # TODAY IS DECEMBER 1, 2025
    # This weekend = Dec 5-7, 2025 (Fri-Sun)
    location = "New York, NY"
    start_date = "2025-12-05"
    end_date = "2025-12-07"

    print("\n" + "="*70)
    print("🗽 NEW YORK CITY CONCERT TEST")
    print("="*70)
    print(f"\n📅 TODAY: December 1, 2025")
    print(f"📅 Weekend: {start_date} to {end_date} (Fri-Sun)")
    print(f"📍 Location: {location}")
    print(f"\n🎯 Goals:")
    print(f"   • Test Songkick event pages")
    print(f"   • Verify Brooklyn concerts are found")
    print(f"   • Test large metro neighborhood strategy")
    print("="*70)

    # Step 1: Context Router
    print(f"\n1️⃣  Context Router...")
    context = analyze_city(location, start_date, end_date)

    print(f"   ✅ {context.location_info.normalized_location}")
    print(f"   🏙️  Classification: {context.area_classification}")
    print(f"   📏 Radius: {context.search_parameters.concert_radius_miles} miles")

    if context.neighborhoods:
        print(f"\n   🏘️  Neighborhoods ({len(context.neighborhoods)}):")
        for n in context.neighborhoods:
            print(f"      • {n}")

    # Step 2: Ticketmaster
    print(f"\n2️⃣  Ticketmaster Tool...")
    ticketmaster_results = get_concerts_ticketmaster(context, start_date, end_date)

    # Step 3: Tavily (Songkick + Bandsintown event pages)
    print(f"\n3️⃣  Tavily Tool (Songkick + Bandsintown event pages)...")
    web_pages = get_concerts_tavily_enhanced(context, start_date, end_date)

    # Step 4: Aggregation
    print(f"\n4️⃣  Aggregation Tool...")
    final_results = aggregate_concerts(
        ticketmaster_results,
        web_pages,
        context,
        start_date,
        end_date
    )

    # Results
    print("\n" + "="*70)
    print("✅ RESULTS")
    print("="*70)

    tm_count = sum(1 for c in final_results.concerts if c.source == "ticketmaster")
    songkick_count = sum(1 for c in final_results.concerts if c.source == "songkick")
    bandsintown_count = sum(1 for c in final_results.concerts if c.source == "bandsintown")
    web_count = sum(1 for c in final_results.concerts if c.source == "web")

    print(f"\n📊 Total Concerts: {final_results.total_count}")
    print(f"\n   Sources:")
    print(f"     • Ticketmaster: {tm_count}")
    print(f"     • Songkick: {songkick_count} ← Testing this!")
    print(f"     • Bandsintown: {bandsintown_count}")
    print(f"     • Web (generic): {web_count}")

    # Geographic diversity - check for Brooklyn!
    if final_results.concerts:
        unique_locations = set(c.location for c in final_results.concerts if c.location)
        print(f"\n🗺️  Geographic Coverage ({len(unique_locations)} unique locations):")

        # Check specifically for Brooklyn
        brooklyn_concerts = [c for c in final_results.concerts if c.location and "Brooklyn" in c.location]
        queens_concerts = [c for c in final_results.concerts if c.location and "Queens" in c.location]
        manhattan_concerts = [c for c in final_results.concerts if c.location and ("Manhattan" in c.location or "New York, NY" in c.location)]

        print(f"\n   📍 Borough Breakdown:")
        print(f"      • Manhattan: {len(manhattan_concerts)} concerts")
        print(f"      • Brooklyn: {len(brooklyn_concerts)} concerts ← Should find some!")
        print(f"      • Queens: {len(queens_concerts)} concerts")

        print(f"\n   All locations:")
        for loc in sorted(unique_locations)[:15]:
            count = sum(1 for c in final_results.concerts if c.location == loc)
            print(f"      • {loc}: {count} concerts")

    # Show sample concerts
    if final_results.concerts:
        print(f"\n🎵 Sample Concerts (first 10):")
        for i, concert in enumerate(final_results.concerts[:10], 1):
            print(f"\n   {i}. {concert.name}")
            print(f"      📍 {concert.venue} ({concert.location})")
            print(f"      📅 {concert.date} {concert.time or ''}")
            print(f"      🔗 Source: {concert.source}")

    # Save results
    import json

    run_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = (
        Path(__file__).parent / "test_results" /
        "New_York_NY" /
        f"run_{run_timestamp}" /
        f"weekend_{start_date}_to_{end_date}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "final_results.json", "w") as f:
        json.dump(final_results.model_dump(), f, indent=2)

    with open(output_dir / "ticketmaster_results.json", "w") as f:
        json.dump({"count": len(ticketmaster_results), "results": ticketmaster_results}, f, indent=2)

    with open(output_dir / "web_pages.json", "w") as f:
        json.dump({
            "page_count": len(web_pages),
            "pages": [{"page_num": i+1, "length": len(p), "preview": p[:500]} for i, p in enumerate(web_pages)]
        }, f, indent=2)

    with open(output_dir / "metadata.json", "w") as f:
        json.dump({
            "run_timestamp": run_timestamp,
            "location": location,
            "normalized_location": context.location_info.normalized_location,
            "area_classification": context.area_classification,
            "neighborhoods": context.neighborhoods,
            "weekend_dates": f"{start_date} to {end_date}",
            "total_concerts_found": final_results.total_count,
            "sources": {
                "ticketmaster": tm_count,
                "songkick": songkick_count,
                "bandsintown": bandsintown_count,
                "web": web_count
            },
            "borough_breakdown": {
                "manhattan": len(manhattan_concerts) if final_results.concerts else 0,
                "brooklyn": len(brooklyn_concerts) if final_results.concerts else 0,
                "queens": len(queens_concerts) if final_results.concerts else 0
            }
        }, f, indent=2)

    print(f"\n💾 Saved to: {output_dir}")
    print(f"   Structure: New_York_NY/run_timestamp/weekend_dates/files")
    print("="*70 + "\n")

    return final_results


if __name__ == "__main__":
    test_new_york()
