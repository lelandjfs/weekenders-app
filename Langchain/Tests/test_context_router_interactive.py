"""
Interactive Context Router Tester
==================================

Simple CLI to test the Context Router with any location and dates.
Run this to see how different locations are classified and routed.
"""

import sys
import os

# Add parent directory to path so we can import context_router
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from context_router import analyze_city, print_context_summary


def test_location_interactive():
    """Interactive testing of Context Router"""

    print("\n" + "="*70)
    print("🌍 WEEKENDERS APP - CONTEXT ROUTER INTERACTIVE TESTER")
    print("="*70)
    print("\nTest how different locations are analyzed and classified.")
    print("Model: Claude 3.5 Haiku (~$0.0003 per query)")
    print("\nType 'quit' or 'exit' to stop.\n")

    while True:
        print("-" * 70)

        # Get location
        location = input("\n📍 Enter location (e.g., 'Austin', 'Palo Alto', 'NYC'): ").strip()

        if location.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!\n")
            break

        if not location:
            print("⚠️  Please enter a location.")
            continue

        # Get dates (with defaults)
        start_date = input("📅 Start date (YYYY-MM-DD) [default: 2024-12-06]: ").strip()
        if not start_date:
            start_date = "2024-12-06"

        end_date = input("📅 End date (YYYY-MM-DD) [default: 2024-12-08]: ").strip()
        if not end_date:
            end_date = "2024-12-08"

        # Analyze
        print(f"\n⏳ Analyzing '{location}' for {start_date} to {end_date}...")
        print("   (Calling Claude 3.5 Haiku...)\n")

        try:
            context = analyze_city(location, start_date, end_date)
            print_context_summary(context)

            # Quick summary
            print("\n" + "="*70)
            print("🎯 QUICK SUMMARY")
            print("="*70)

            if context.area_classification == "too_large":
                print(f"\n✅ {context.location_info.normalized_location} is TOO LARGE")
                print(f"   Strategy: Search {len(context.neighborhoods)} trendy neighborhoods")
                print(f"   Dining radius: {context.search_parameters.dining_radius_miles} miles per neighborhood")
                print(f"\n   Neighborhoods:")
                for n in context.neighborhoods:
                    print(f"     • {n}")

            elif context.area_classification == "too_small":
                print(f"\n✅ {context.location_info.normalized_location} is TOO SMALL")
                print(f"   Strategy: Expand to {len(context.expanded_areas)} nearby areas")
                print(f"   Dining radius: {context.search_parameters.dining_radius_miles} miles (wide net)")
                print(f"\n   Expanded Areas:")
                for a in context.expanded_areas:
                    print(f"     • {a}")

            else:
                print(f"\n✅ {context.location_info.normalized_location} is APPROPRIATE SIZE")
                print(f"   Strategy: City-wide search")
                print(f"   Dining radius: {context.search_parameters.dining_radius_miles} miles")

            print(f"\n   Concert radius: {context.search_parameters.concert_radius_miles} miles")
            print(f"   Coordinates: {context.location_info.latitude}, {context.location_info.longitude}")

        except Exception as e:
            print(f"\n❌ Error analyzing location: {e}")
            print("   Try another location.\n")
            continue

        # Ask if they want to test another
        print("\n" + "="*70)
        another = input("\n🔄 Test another location? (y/n) [y]: ").strip().lower()
        if another and another not in ['y', 'yes', '']:
            print("\n👋 Done testing!\n")
            break


def quick_test_examples():
    """Quick test with example locations"""

    print("\n" + "="*70)
    print("🚀 QUICK TEST - Example Locations")
    print("="*70)
    print("\nTesting 6 different location types:\n")

    examples = [
        ("New York City", "Large metro - should break into neighborhoods"),
        ("Los Angeles", "Large metro - should break into neighborhoods"),
        ("Austin, Texas", "Medium city - should search city-wide"),
        ("Portland, Oregon", "Medium city - should search city-wide"),
        ("Palo Alto, CA", "Small area - should expand to nearby cities"),
        ("Santa Monica", "Small area - should expand to LA area"),
    ]

    for i, (location, description) in enumerate(examples, 1):
        print(f"\n{i}. {location}")
        print(f"   Expected: {description}")
        print(f"   Analyzing...\n")

        context = analyze_city(location, "2024-12-06", "2024-12-08")

        # Print compact summary
        print(f"   ✅ Classification: {context.area_classification.upper()}")
        print(f"   📍 Normalized: {context.location_info.normalized_location}")
        print(f"   🗺️  Coordinates: {context.location_info.latitude}, {context.location_info.longitude}")

        if context.area_classification == "too_large":
            print(f"   🏘️  Neighborhoods: {len(context.neighborhoods)}")
            print(f"       {', '.join(context.neighborhoods[:3])}...")
        elif context.area_classification == "too_small":
            print(f"   📍 Expanded: {len(context.expanded_areas)}")
            print(f"       {', '.join(context.expanded_areas[:3])}...")
        else:
            print(f"   ✓  City-wide search")

        print(f"   📏 Dining: {context.search_parameters.dining_radius_miles}mi, Concerts: {context.search_parameters.concert_radius_miles}mi")
        print("-" * 70)

    print(f"\n✅ Tested {len(examples)} locations")
    print(f"💰 Estimated cost: ~${len(examples) * 0.0003:.4f}")


if __name__ == "__main__":
    import sys

    # Check if user wants quick test or interactive
    if len(sys.argv) > 1 and sys.argv[1] in ['quick', 'examples', 'demo']:
        quick_test_examples()
    else:
        print("\n💡 TIP: Run with 'python test_context_router_interactive.py quick' for automated examples")
        test_location_interactive()
