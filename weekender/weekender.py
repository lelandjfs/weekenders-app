#!/usr/bin/env python3
"""
Weekender - Trip Discovery CLI
===============================

Interactive CLI tool to find concerts, restaurants, events, and locations
for your weekend trip.

Usage:
    python weekender.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from runner import run_all_agents, get_weekend_dates


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print the CLI header."""
    print()
    print("+" + "-" * 41 + "+")
    print("|  WEEKENDER - Weekend Trip Planner       |")
    print("+" + "-" * 41 + "+")
    print()


def get_user_input():
    """Get city and weekend from user."""
    city = input("  City: ").strip()
    if not city:
        print("  City is required")
        return None, None

    weekend_input = input("  Weekend (next/this) [next]: ").strip().lower()
    weekend = weekend_input if weekend_input in ["next", "this"] else "next"

    return city, weekend


def format_date_range(start_date: str, end_date: str) -> str:
    """Format date range for display."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    return f"{start.strftime('%a %b %d')} - {end.strftime('%a %b %d, %Y')}"


def format_time(time_str):
    """Format time string nicely."""
    if not time_str:
        return ""
    try:
        if ":" in str(time_str):
            t = datetime.strptime(str(time_str)[:5], "%H:%M")
            return t.strftime(" @ %I:%M %p").replace(" 0", " ")
    except:
        pass
    return f" @ {time_str}" if time_str else ""


def format_date(date_str):
    """Format date string nicely."""
    if not date_str:
        return "TBD"
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%a %b %d")
    except:
        return date_str


def print_section_header(title: str, count: int):
    """Print a section header."""
    print()
    print("=" * 60)
    print(f"  {title} ({count} found)")
    print("=" * 60)


def print_concerts(concerts: list):
    """Print concert results."""
    print_section_header("CONCERTS", len(concerts))

    if not concerts:
        print("  No concerts found for these dates.")
        return

    for i, concert in enumerate(concerts, 1):
        name = concert.get('name', 'Unknown')
        venue = concert.get('venue', 'TBD')
        date = format_date(concert.get('date', ''))
        time = format_time(concert.get('time', ''))
        source = concert.get('source', 'unknown')
        url = concert.get('url', '')

        print(f"\n  {i}. {name}")
        print(f"     Venue: {venue}")
        print(f"     Date:  {date}{time}")
        print(f"     Source: {source}")
        if url:
            print(f"     URL: {url[:55]}...")


def print_dining(restaurants: list):
    """Print dining results."""
    print_section_header("DINING", len(restaurants))

    if not restaurants:
        print("  No restaurants found.")
        return

    for i, restaurant in enumerate(restaurants, 1):
        name = restaurant.get('name', 'Unknown')
        neighborhood = restaurant.get('neighborhood', '')
        cuisine = restaurant.get('cuisine', '')
        rating = restaurant.get('rating', '')
        price = restaurant.get('price_level', '')
        source = restaurant.get('source', 'unknown')

        print(f"\n  {i}. {name}")
        if neighborhood:
            print(f"     Neighborhood: {neighborhood}")
        if cuisine:
            print(f"     Cuisine: {cuisine}")
        if rating:
            print(f"     Rating: {rating}")
        if price:
            print(f"     Price: {price}")
        print(f"     Source: {source}")


def print_events(events: list):
    """Print events results."""
    print_section_header("EVENTS", len(events))

    if not events:
        print("  No events found for these dates.")
        return

    for i, event in enumerate(events, 1):
        name = event.get('name', 'Unknown')
        venue = event.get('venue', 'TBD')
        date = format_date(event.get('date', ''))
        time = format_time(event.get('time', ''))
        category = event.get('category', '')
        source = event.get('source', 'unknown')
        url = event.get('url', '')

        print(f"\n  {i}. {name}")
        if venue:
            print(f"     Venue: {venue}")
        print(f"     Date:  {date}{time}")
        if category:
            print(f"     Category: {category}")
        print(f"     Source: {source}")
        if url:
            print(f"     URL: {url[:55]}...")


def print_locations(locations: list):
    """Print locations results."""
    print_section_header("LOCATIONS & ATTRACTIONS", len(locations))

    if not locations:
        print("  No locations found.")
        return

    for i, location in enumerate(locations, 1):
        name = location.get('name', 'Unknown')
        category = location.get('category', '')
        description = location.get('description', '')
        rating = location.get('rating', '')
        source = location.get('source', 'unknown')

        print(f"\n  {i}. {name}")
        if category:
            print(f"     Category: {category}")
        if description:
            desc = description[:80] + "..." if len(description) > 80 else description
            print(f"     Info: {desc}")
        if rating:
            print(f"     Rating: {rating}")
        print(f"     Source: {source}")


def print_summary(results: dict):
    """Print summary of all results."""
    print()
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Concerts:  {len(results['concerts'])}")
    print(f"  Dining:    {len(results['dining'])}")
    print(f"  Events:    {len(results['events'])}")
    print(f"  Locations: {len(results['locations'])}")

    if results['errors']:
        print()
        print("  Errors:")
        for err in results['errors']:
            print(f"    - {err['agent']}: {err['error'][:50]}...")


def main():
    """Main CLI entry point."""
    clear_screen()
    print_header()

    # Get user input
    city, weekend = get_user_input()
    if not city:
        return

    # Calculate dates
    start_date, end_date = get_weekend_dates(weekend)
    date_range = format_date_range(start_date, end_date)

    print()
    print(f"  Dates: {date_range}")
    print()
    print("-" * 60)
    print("  Searching all categories... (this may take a few minutes)")
    print("  Running 4 agents in parallel:")
    print("    - Concert Agent")
    print("    - Dining Agent")
    print("    - Events Agent")
    print("    - Locations Agent")
    print("-" * 60)

    try:
        results = run_all_agents(city=city, weekend=weekend)

        # Print all categories
        print_concerts(results['concerts'])
        print_dining(results['dining'])
        print_events(results['events'])
        print_locations(results['locations'])
        print_summary(results)

    except KeyboardInterrupt:
        print("\n\n  Cancelled by user.")
    except Exception as e:
        print(f"\n  Error: {e}")
        import traceback
        traceback.print_exc()

    print()


if __name__ == "__main__":
    main()
