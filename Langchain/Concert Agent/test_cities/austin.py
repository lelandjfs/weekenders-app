"""
Weekend Concert Test
====================

Test Concert Agent for this weekend with improved parsing.

Focus:
- Narrow date range (just the weekend)
- Songkick + Bandsintown only
- Improved Claude parsing for date-grouped concerts
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

def test_weekend_concerts():
    """Test with this weekend's dates"""

    # TODAY IS DECEMBER 1, 2025
    # This weekend = Dec 5-7, 2025 (Fri-Sun)
    location = "Austin, Texas"
    start_date = "2025-12-05"  # This Friday
    end_date = "2025-12-07"    # This Sunday

    print("\n" + "="*70)
    print("🎸 WEEKEND CONCERT TEST")
    print("="*70)
    print(f"\n📅 TODAY: December 1, 2025")
    print(f"📅 Date Range: {start_date} to {end_date} (This Weekend: Fri-Sun)")
    print(f"📍 Location: {location}")
    print(f"\n🎯 Goal: Extract ALL concerts from Songkick/Bandsintown for this weekend")
    print("="*70)

    # Step 1: Context Router
    print(f"\n1️⃣  Context Router...")
    context = analyze_city(location, start_date, end_date)
    print(f"   ✅ {context.location_info.normalized_location}")
    print(f"   📏 Radius: {context.search_parameters.concert_radius_miles} miles")

    # Step 2: Ticketmaster
    print(f"\n2️⃣  Ticketmaster Tool...")
    ticketmaster_results = get_concerts_ticketmaster(context, start_date, end_date)

    # Step 3: Tavily (Songkick + Bandsintown)
    print(f"\n3️⃣  Tavily Tool (Songkick + Bandsintown)...")
    web_pages = get_concerts_tavily_enhanced(context, start_date, end_date)

    # Show preview of what we extracted
    if web_pages:
        print(f"\n   📄 Extracted Pages Preview:")
        for i, page in enumerate(web_pages[:3], 1):
            lines = page.split('\n')[:10]  # First 10 lines
            source_url = lines[0].replace('SOURCE: ', '') if lines else 'Unknown'
            print(f"\n   Page {i}: {source_url}")
            print(f"   Length: {len(page)} chars")
            # Show a snippet of concert listings
            for line in lines[1:6]:
                if line.strip():
                    print(f"     {line[:80]}")

    # Step 4: Aggregation
    print(f"\n4️⃣  Aggregation Tool (parsing {len(web_pages)} pages)...")
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
    print(f"\n📊 Summary:")
    print(f"   Total Concerts: {final_results.total_count}")
    print(f"   Ticketmaster: {len(ticketmaster_results)}")
    print(f"   Web Pages Parsed: {len(web_pages)}")

    tm_count = sum(1 for c in final_results.concerts if c.source == "ticketmaster")
    web_count = sum(1 for c in final_results.concerts if c.source == "web")
    print(f"\n   Breakdown:")
    print(f"     • From Ticketmaster: {tm_count}")
    print(f"     • From Web: {web_count}")

    # Show all concerts
    if final_results.concerts:
        print(f"\n🎵 All Concerts Found ({final_results.total_count}):")
        for i, concert in enumerate(final_results.concerts, 1):
            print(f"\n   {i}. {concert.name}")
            print(f"      📍 {concert.venue}")
            print(f"      📅 {concert.date} {concert.time or ''}")
            if concert.price_range:
                print(f"      💰 {concert.price_range}")
            print(f"      🔗 Source: {concert.source}")
    else:
        print("\n⚠️  No concerts found!")

    print("\n" + "="*70)

    # Save results with schema: location -> date_of_run -> weekend_dates -> files
    import json

    run_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = (
        Path(__file__).parent / "test_results" /
        "Austin_Texas" /
        f"run_{run_timestamp}" /
        f"weekend_{start_date}_to_{end_date}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save all results
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
            "weekend_dates": f"{start_date} to {end_date}",
            "total_concerts_found": final_results.total_count,
            "sources": {"ticketmaster": tm_count, "web": web_count}
        }, f, indent=2)

    print(f"\n💾 Saved to: {output_dir}")
    print(f"   Structure: location/run_timestamp/weekend_dates/files")
    print("="*70 + "\n")

    return final_results


if __name__ == "__main__":
    test_weekend_concerts()
