"""
Content Filter Utilities
=========================

Pre-filters raw web content to extract only relevant sections before sending to LLM.
Reduces context window usage by 60-80% while preserving important information.
"""

import re
from typing import List, Tuple


def filter_restaurant_content(raw_content: str, max_lines: int = 150) -> str:
    """
    Extract restaurant-relevant content from raw markdown.

    Looks for:
    - Restaurant names (bold text, numbered lists)
    - Addresses and locations
    - Price indicators ($, $$, $$$)
    - Ratings and reviews
    - Cuisine types
    - Descriptions with food keywords
    """
    lines = raw_content.split('\n')
    relevant_lines = []

    # Patterns that indicate restaurant content
    patterns = [
        r'\*\*[A-Z].*\*\*',           # Bold text (often restaurant names)
        r'^\s*\d+[\.\)]\s+\*?\*?[A-Z]', # Numbered lists
        r'\$+\s*[-–]?\s*\$*',          # Price ranges ($, $$-$$$)
        r'\d+(\.\d+)?\s*(stars?|rating|/\s*5|/\s*10)', # Ratings
        r'(address|location|located|neighborhood)[:|\s]', # Location info
        r'(cuisine|serves?|specializ|known for)',  # Cuisine type
        r'(reservations?|book|hours|open)',  # Practical info
        r'(menu|dishes?|plates?|appetizer|entree|dessert)', # Food terms
        r'(chef|kitchen|restaurant|eatery|bistro|cafe|bar)', # Venue terms
        r'(delicious|amazing|best|popular|favorite|must.?try)', # Recommendations
        r'https?://[^\s]+',            # URLs (often to restaurant sites)
    ]

    # Compile patterns for efficiency
    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]

    # Track context - keep lines before/after matches
    match_indices = set()

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped or len(line_stripped) < 5:
            continue

        # Check if line matches any pattern
        for pattern in compiled:
            if pattern.search(line):
                # Add this line and surrounding context
                match_indices.update(range(max(0, i-1), min(len(lines), i+3)))
                break

    # Collect relevant lines
    for i in sorted(match_indices):
        if i < len(lines):
            relevant_lines.append(lines[i])

    # Cap at max_lines
    if len(relevant_lines) > max_lines:
        relevant_lines = relevant_lines[:max_lines]

    return '\n'.join(relevant_lines)


def filter_event_content(raw_content: str, max_lines: int = 150) -> str:
    """
    Extract event-relevant content from raw markdown.

    Looks for:
    - Event names and titles
    - Dates and times
    - Venues and locations
    - Ticket prices
    - Event categories (sports, arts, family, etc.)
    """
    lines = raw_content.split('\n')
    relevant_lines = []

    patterns = [
        r'\*\*[A-Z].*\*\*',           # Bold text (event names)
        r'^\s*\d+[\.\)]\s+\*?\*?[A-Z]', # Numbered lists
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d', # Dates
        r'\d{1,2}[/\-]\d{1,2}[/\-]?\d{0,4}', # Date formats
        r'\d{1,2}:\d{2}\s*(am|pm|AM|PM)?', # Times
        r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', # Days
        r'\$\d+',                      # Ticket prices
        r'(tickets?|admission|entry|free)',  # Ticket info
        r'(venue|location|at the|held at|takes place)', # Venue info
        r'(festival|fair|exhibition|show|performance|game|match)', # Event types
        r'(sports?|arts?|theater|theatre|comedy|family|kids)', # Categories
        r'(annual|weekly|daily|special|limited)', # Event qualifiers
        r'https?://[^\s]+',            # URLs
    ]

    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
    match_indices = set()

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped or len(line_stripped) < 5:
            continue

        for pattern in compiled:
            if pattern.search(line):
                match_indices.update(range(max(0, i-1), min(len(lines), i+3)))
                break

    for i in sorted(match_indices):
        if i < len(lines):
            relevant_lines.append(lines[i])

    if len(relevant_lines) > max_lines:
        relevant_lines = relevant_lines[:max_lines]

    return '\n'.join(relevant_lines)


def filter_location_content(raw_content: str, max_lines: int = 150) -> str:
    """
    Extract location/attraction-relevant content from raw markdown.

    Looks for:
    - Attraction names
    - Addresses and neighborhoods
    - Hours of operation
    - Admission prices
    - Categories (museum, park, landmark, etc.)
    - Descriptions and highlights
    """
    lines = raw_content.split('\n')
    relevant_lines = []

    patterns = [
        r'\*\*[A-Z].*\*\*',           # Bold text (place names)
        r'^\s*\d+[\.\)]\s+\*?\*?[A-Z]', # Numbered lists
        r'(address|location|located|neighborhood|district)', # Location
        r'(hours|open|closed|daily|weekends?)', # Hours
        r'\$\d+|free\s*(admission|entry)?', # Pricing
        r'(museum|gallery|park|garden|landmark|monument)', # Attraction types
        r'(historic|famous|popular|iconic|hidden gem)', # Descriptors
        r'(tour|visit|explore|see|experience)', # Activity verbs
        r'(architecture|art|nature|wildlife|scenic)', # Features
        r'(neighborhood|district|area|quarter)', # Areas
        r'(tip|recommend|must.?see|don\'t miss)', # Recommendations
        r'https?://[^\s]+',            # URLs
    ]

    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
    match_indices = set()

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped or len(line_stripped) < 5:
            continue

        for pattern in compiled:
            if pattern.search(line):
                match_indices.update(range(max(0, i-1), min(len(lines), i+3)))
                break

    for i in sorted(match_indices):
        if i < len(lines):
            relevant_lines.append(lines[i])

    if len(relevant_lines) > max_lines:
        relevant_lines = relevant_lines[:max_lines]

    return '\n'.join(relevant_lines)


def filter_concert_content(raw_content: str, max_lines: int = 150) -> str:
    """
    Extract concert/music-relevant content from raw markdown.

    Looks for:
    - Artist/band names
    - Venue names
    - Dates and times
    - Ticket prices
    - Music genres
    """
    lines = raw_content.split('\n')
    relevant_lines = []

    patterns = [
        r'\*\*[A-Z].*\*\*',           # Bold text (artist names)
        r'^\s*\d+[\.\)]\s+\*?\*?[A-Z]', # Numbered lists
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d', # Dates
        r'\d{1,2}[/\-]\d{1,2}[/\-]?\d{0,4}', # Date formats
        r'\d{1,2}:\d{2}\s*(am|pm|AM|PM)?', # Times
        r'(doors|show|starts?)\s*(at|@)?\s*\d', # Show times
        r'\$\d+',                      # Ticket prices
        r'(tickets?|sold out|on sale|presale)', # Ticket info
        r'(venue|club|theater|theatre|hall|arena|stadium)', # Venues
        r'(concert|show|gig|performance|tour|live)', # Event types
        r'(rock|pop|jazz|blues|country|hip.?hop|electronic|indie|metal|folk|r&b)', # Genres
        r'(band|artist|musician|dj|performer|singer)', # Performer terms
        r'(opening act|headlin|support)', # Show structure
        r'https?://[^\s]+',            # URLs
    ]

    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
    match_indices = set()

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped or len(line_stripped) < 5:
            continue

        for pattern in compiled:
            if pattern.search(line):
                match_indices.update(range(max(0, i-1), min(len(lines), i+3)))
                break

    for i in sorted(match_indices):
        if i < len(lines):
            relevant_lines.append(lines[i])

    if len(relevant_lines) > max_lines:
        relevant_lines = relevant_lines[:max_lines]

    return '\n'.join(relevant_lines)


def filter_content(raw_content: str, content_type: str, max_lines: int = 150) -> str:
    """
    Filter content based on type.

    Args:
        raw_content: Raw markdown content from Tavily
        content_type: One of 'restaurants', 'events', 'locations', 'concerts'
        max_lines: Maximum lines to return

    Returns:
        Filtered content with only relevant sections
    """
    filters = {
        'restaurants': filter_restaurant_content,
        'dining': filter_restaurant_content,
        'events': filter_event_content,
        'locations': filter_location_content,
        'attractions': filter_location_content,
        'concerts': filter_concert_content,
        'music': filter_concert_content,
    }

    filter_func = filters.get(content_type.lower(), lambda x, m: x[:5000])
    return filter_func(raw_content, max_lines)


def batch_pages(pages: List[str], batch_size: int = 3) -> List[List[str]]:
    """
    Split pages into batches for parallel processing.

    Args:
        pages: List of page contents
        batch_size: Number of pages per batch

    Returns:
        List of batches
    """
    return [pages[i:i+batch_size] for i in range(0, len(pages), batch_size)]


def estimate_tokens(text: str) -> int:
    """Rough estimate of token count (4 chars per token average)."""
    return len(text) // 4
