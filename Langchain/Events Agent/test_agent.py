"""
Test script for LangChain Events Agent
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langsmith import traceable

from config import setup_langsmith
from date_utils import get_events_weekend_dates, get_weekend_dates_for_display
from tools.ticketmaster import search_ticketmaster_events
from tools.web_search import search_web_events
from tools.aggregation import aggregate_events


@dataclass
class EventsResult:
    """Structured result from events agent."""
    city: str
    start_date: str
    end_date: str
    total_events: int
    events: List[Dict[str, Any]]
    sources: Dict[str, int]
    categories: Dict[str, int]
    execution_time_seconds: float
    timestamp: str


class EventsAgent:
    """LangChain-compatible events discovery agent."""

    def __init__(
        self,
        project_name: str = "weekenders-events-agent",
        enable_tracing: bool = True,
        output_dir: str = None
    ):
        self.project_name = project_name
        self.enable_tracing = enable_tracing
        self.output_dir = output_dir or str(Path(__file__).parent / "tests")
        setup_langsmith(project_name, enable_tracing)

    @traceable(name="events_agent_run")
    def run(
        self,
        city: str,
        weekend: str = "next",
        start_date: str = None,
        end_date: str = None,
        save_results: bool = True
    ) -> EventsResult:
        """
        Run the events agent for a city.

        Args:
            city: City name (e.g., "San Francisco", "Sacramento")
            weekend: "next" or "this" for automatic date calculation
            start_date: Override start date (YYYY-MM-DD)
            end_date: Override end date (YYYY-MM-DD)
            save_results: Whether to save results to disk

        Returns:
            EventsResult with all discovered events
        """
        start_time = datetime.now()
        timestamp = start_time.isoformat()

        # Calculate dates if not provided
        if not start_date or not end_date:
            start_date, end_date = get_events_weekend_dates(weekend)

        print(f"\n{'='*60}")
        print(f"🎭 EVENTS AGENT - {city.upper()}")
        print(f"{'='*60}")
        print(f"📅 {get_weekend_dates_for_display(weekend)}")
        print(f"   ({start_date} to {end_date})")

        # Step 1: Search Ticketmaster for non-music events
        print(f"\n🎫 Step 1: Searching Ticketmaster...")
        ticketmaster_results = search_ticketmaster_events.invoke({
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
            "radius_miles": 25
        })

        # Step 2: Search web sources
        print(f"\n🌐 Step 2: Searching web sources...")
        web_pages = search_web_events.invoke({
            "city": city,
            "start_date": start_date,
            "end_date": end_date
        })

        # Step 3: Aggregate and deduplicate
        print(f"\n🤖 Step 3: Aggregating results...")
        events = aggregate_events.invoke({
            "ticketmaster_results": ticketmaster_results,
            "web_page_contents": web_pages,
            "city": city,
            "start_date": start_date,
            "end_date": end_date
        })

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Count sources and categories
        source_counts = {}
        category_counts = {}
        for e in events:
            source = e.get("source", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1

            category = e.get("category", "Other")
            category_counts[category] = category_counts.get(category, 0) + 1

        # Build result
        result = EventsResult(
            city=city,
            start_date=start_date,
            end_date=end_date,
            total_events=len(events),
            events=events,
            sources=source_counts,
            categories=category_counts,
            execution_time_seconds=execution_time,
            timestamp=timestamp
        )

        # Save results if requested
        if save_results:
            self._save_results(result)

        # Print summary
        self._print_summary(result)

        return result

    def _save_results(self, result: EventsResult):
        """Save results to a timestamped file."""
        city_folder = result.city.replace(" ", "_")
        output_path = Path(self.output_dir) / city_folder
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"run_{timestamp}.json"
        filepath = output_path / filename

        with open(filepath, "w") as f:
            json.dump(asdict(result), f, indent=2, default=str)

        print(f"\n📁 Results saved to: {filepath}")

    def _print_summary(self, result: EventsResult):
        """Print a summary of results."""
        print(f"\n{'='*60}")
        print(f"✅ EVENTS AGENT COMPLETE")
        print(f"{'='*60}")
        print(f"   City: {result.city}")
        print(f"   Date Range: {result.start_date} to {result.end_date}")
        print(f"   Total Events: {result.total_events}")
        print(f"   Sources: {result.sources}")
        print(f"   Categories: {result.categories}")
        print(f"   Execution Time: {result.execution_time_seconds:.2f}s")
        print(f"{'='*60}")

        if result.events:
            print(f"\n🎭 TOP 10 EVENTS:")
            for i, e in enumerate(result.events[:10], 1):
                name = e.get("name", "Unknown")
                venue = e.get("venue", "")
                date = e.get("date", "TBD")
                category = e.get("category", "")
                source = e.get("source", "")

                print(f"   {i}. {name}")
                if venue:
                    print(f"      📍 {venue}")
                print(f"      📅 {date} | {category} | {source}")

        print(f"\n{'='*60}\n")


def run_events_agent(city: str, weekend: str = "next") -> EventsResult:
    """Convenience function to run the events agent."""
    agent = EventsAgent()
    return agent.run(city, weekend=weekend)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test the LangChain Events Agent")
    parser.add_argument("city", help="City to search (e.g., 'Austin', 'Sacramento')")
    parser.add_argument("--weekend", "-w", type=str, default="next",
                       choices=["this", "next"],
                       help="Which weekend (default: next)")

    args = parser.parse_args()

    print(f"\n🎭 Testing LangChain Events Agent for: {args.city}")
    print(f"   Weekend: {args.weekend}")

    result = run_events_agent(args.city, weekend=args.weekend)
    print(f"\nTotal: {result.total_events} events")
