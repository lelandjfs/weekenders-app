"""
Test Runner for Dining Agent
==============================

Runs the dining agent and saves results with timestamps.
Each run creates a new file, never overwriting previous runs.

Output structure:
    tests/
    └── San_Francisco/
        └── run_20251225_140000.json
        └── run_20251225_150000.json
    └── Austin/
        └── run_20251225_141500.json
"""

import os
import json
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dining_agent import DiningAgent


def run_test(city: str, cuisine_type: str = None) -> dict:
    """
    Run the dining agent for a city and save results.

    Args:
        city: City name to search
        cuisine_type: Optional cuisine filter

    Returns:
        Result dictionary
    """
    # Initialize agent
    agent = DiningAgent()

    # Run the agent
    result = agent.run(city, cuisine_type=cuisine_type)

    # Save results
    save_results(result, city)

    # Print formatted output
    print(agent.format_results(result))

    return result


def save_results(result: dict, city: str):
    """
    Save results to a timestamped file.

    Creates a new file for each run, never overwriting.
    """
    # Create city folder (replace spaces with underscores)
    city_folder = city.replace(" ", "_")
    tests_dir = os.path.join(os.path.dirname(__file__), "tests", city_folder)
    os.makedirs(tests_dir, exist_ok=True)

    # Create timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"run_{timestamp}.json"
    filepath = os.path.join(tests_dir, filename)

    # Save to file
    with open(filepath, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n📁 Results saved to: {filepath}")

    return filepath


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test the Dining Agent")
    parser.add_argument("city", nargs="?", default="San Francisco",
                       help="City to search (default: San Francisco)")
    parser.add_argument("--cuisine", "-c", type=str, default=None,
                       help="Cuisine type filter (e.g., Italian, Mexican)")

    args = parser.parse_args()

    print(f"\n🍽️  Testing Dining Agent for: {args.city}")
    if args.cuisine:
        print(f"   Cuisine filter: {args.cuisine}")
    print()

    result = run_test(args.city, cuisine_type=args.cuisine)

    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"   City: {result['city']}")
    print(f"   Total Restaurants: {result['total_restaurants']}")
    print(f"   Neighborhoods: {len(result.get('neighborhoods', []))}")
    print(f"   Sources: {result.get('sources', {})}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
