# Testing the Context Router

## Interactive Testing (Try Your Own Locations!)

Run the interactive tester to try any location you want:

```bash
cd "/Users/lelandspeth/Data Initiatives/weekenders_app/Langchain/Tests"
python3 test_context_router_interactive.py
```

This will prompt you for:
1. **Location** - Any city, suburb, or area (e.g., "Miami", "Hoboken", "Tokyo")
2. **Start Date** - Press enter for default (2024-12-06) or enter your own (YYYY-MM-DD)
3. **End Date** - Press enter for default (2024-12-08) or enter your own

### Example Session:

```
📍 Enter location: Miami
📅 Start date (YYYY-MM-DD) [default: 2024-12-06]:
📅 End date (YYYY-MM-DD) [default: 2024-12-08]:

⏳ Analyzing 'Miami' for 2024-12-06 to 2024-12-08...

[Shows full analysis with neighborhoods/expanded areas, coordinates, radii, etc.]

🔄 Test another location? (y/n) [y]: y

📍 Enter location: Hoboken, NJ
...
```

Type `quit` or `exit` to stop.

---

## Quick Test (Automated Examples)

Run with preset examples to see all 3 scenarios:

```bash
python3 test_context_router_interactive.py quick
```

This tests:
- **TOO LARGE**: NYC, LA (shows neighborhood breakdown)
- **APPROPRIATE SIZE**: Austin, Portland (shows city-wide strategy)
- **TOO SMALL**: Palo Alto, Santa Monica (shows expanded areas)

---

## What Gets Analyzed

For each location, the Context Router provides:

### 📍 Location Understanding
- Original input vs normalized location
- Lat/long coordinates
- Country identification

### 🎯 Classification
- **Area Type**: `too_large`, `appropriate_size`, or `too_small`
- **City Type**: `large_metro`, `medium_city`, or `small_area`
- **Search Scope**: What we're actually searching

### 🗺️ Search Strategy
**If TOO LARGE** (like NYC):
- Lists 4-6 trendy neighborhoods
- Tight radius per neighborhood (1.5 miles)
- Wide radius for concerts (25 miles)

**If APPROPRIATE SIZE** (like Austin):
- City-wide search
- Medium radius (5-7 miles)
- Medium concert radius (20 miles)

**If TOO SMALL** (like Palo Alto):
- Lists 3-5 nearby expanded areas
- Wide radius (10-15 miles)
- Very wide concert radius (30-40 miles)

### 📏 Search Radii
- Dining radius
- Concert radius (always wider - people travel for shows!)
- Events radius
- Locations radius

### 💡 Reasoning
Claude explains why it made its classification decisions

---

## Cost

- **~$0.0003 per query** (Claude 3.5 Haiku)
- Testing 10 locations ≈ $0.003 (basically free)

---

## Next Steps

Once you've tested locations and understand how routing works:

1. Move to building individual agents (Concert, Dining, Events, Locations)
2. Each agent will receive the context object and adapt its search accordingly
3. Wire everything together in the main orchestration workflow

---

## Example Use Cases

### For Your Home City (Automated Weekend Emails)
```python
# Set default location once
context = analyze_city("Austin, Texas", "2024-12-06", "2024-12-08")
# Use this context to run all agents weekly
```

### For Travel (Manual Input)
```python
# User traveling to new city
location = input("Where are you going?")
dates = input("What dates?")
context = analyze_city(location, start_date, end_date)
# Agents adapt to that city's characteristics
```

### Testing Different Cities
Use the interactive tester to see how classification works for:
- Your home city
- Cities you're planning to visit
- Edge cases (suburbs, international cities, small towns)
