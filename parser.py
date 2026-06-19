from config import DEFAULT_CURRENCY_SIGN
from geocoder import get_coordinates


def validate_itinerary(itinerary: dict, total_budget: float) -> dict:
    """
    Validates and cleans the itinerary JSON returned by the LLM.

    Checks:
    - All required keys exist
    - Each day has activities
    - Each activity has required fields
    - Grand total doesn't exceed budget
    - Fills in missing optional fields with safe defaults

    Args:
        itinerary    : raw dict from llm_client.call_llm()
        total_budget : the original budget cap to check against

    Returns:
        Cleaned and validated itinerary dict

    Raises:
        ValueError if the itinerary is missing critical structure
    """

    # ── Top level keys ────────────────────────────────────────────────────────
    required_top = ["city", "days", "days_plan", "grand_total"]
    for key in required_top:
        if key not in itinerary:
            raise ValueError(f"Itinerary missing required key: '{key}'")

    if not isinstance(itinerary["days_plan"], list) or len(itinerary["days_plan"]) == 0:
        raise ValueError("Itinerary 'days_plan' is empty or not a list")

    city_name = itinerary.get("city", "")

    # ── Per day validation ────────────────────────────────────────────────────
    for day_obj in itinerary["days_plan"]:

        if "day" not in day_obj:
            raise ValueError("A day entry is missing the 'day' number")

        if "activities" not in day_obj or not isinstance(day_obj["activities"], list):
            raise ValueError(f"Day {day_obj.get('day')} is missing activities list")

        # Fill optional day fields with safe defaults
        day_obj.setdefault("theme", f"Day {day_obj['day']}")
        day_obj.setdefault("day_total", sum(
            a.get("cost", 0) for a in day_obj["activities"]
        ))

        # ── Per activity validation ───────────────────────────────────────────
        for activity in day_obj["activities"]:
            activity.setdefault("name",     "Unnamed Activity")
            activity.setdefault("time",     "TBD")
            activity.setdefault("cost",     0)
            activity.setdefault("category", "activity")
            activity.setdefault("tip",      "Enjoy responsibly!")

            # Make sure cost is a number
            try:
                activity["cost"] = float(activity["cost"])
            except (ValueError, TypeError):
                activity["cost"] = 0.0

            # Validate or fallback geocode coordinates
            has_valid_coords = False
            if "lat" in activity and "lng" in activity:
                try:
                    activity["lat"] = float(activity["lat"])
                    activity["lng"] = float(activity["lng"])
                    if abs(activity["lat"]) > 0.1 and abs(activity["lng"]) > 0.1:
                        has_valid_coords = True
                except (ValueError, TypeError):
                    pass
            
            if not has_valid_coords:
                # Fallback to geocoding activity name
                name = activity["name"]
                # Exclude brackets or text like "(Museum)" for better search
                clean_name = name.split("(")[0].split("-")[0].strip()
                # Run geocoder
                coords = get_coordinates(f"{clean_name}, {city_name}, India")
                if coords:
                    activity["lat"] = coords["lat"]
                    activity["lng"] = coords["lng"]
                else:
                    # Try just with city_name if it fails, or leave it out
                    print(f"[parser] Warning: Could not geocode '{name}' for mapping.")

    # ── Budget check ──────────────────────────────────────────────────────────
    grand_total = itinerary.get("grand_total", 0)
    itinerary.setdefault("savings_tip", "Plan ahead and book early for best rates!")
    itinerary.setdefault("budget_used_percent",
        round((grand_total / total_budget) * 100, 1) if total_budget > 0 else 0
    )

    if grand_total > total_budget * 1.05:   # allow 5% tolerance
        print(
            f"[parser] Warning: grand_total {DEFAULT_CURRENCY_SIGN}{grand_total:,.0f} "
            f"exceeds budget {DEFAULT_CURRENCY_SIGN}{total_budget:,.0f}"
        )

    # ── Budget Upgrades validation ────────────────────────────────────────────
    upgrades = itinerary.get("budget_upgrades", [])
    valid_upgrades = []
    if isinstance(upgrades, list):
        for item in upgrades:
            if isinstance(item, dict) and "name" in item:
                item.setdefault("extra_cost", 0.0)
                try:
                    item["extra_cost"] = float(item["extra_cost"])
                except (ValueError, TypeError):
                    item["extra_cost"] = 0.0
                item.setdefault("description", "Alternative suggestion.")
                valid_upgrades.append(item)
    itinerary["budget_upgrades"] = valid_upgrades

    # ── Transit validation ────────────────────────────────────────────────────
    transit = itinerary.get("transit_to_next_city")
    if isinstance(transit, dict):
        transit.setdefault("next_city", "")
        transit.setdefault("flight_cost_estimation", "N/A")
        transit.setdefault("train_cost_estimation", "N/A")
        transit.setdefault("alternative_cost_estimation", "N/A")
        transit.setdefault("recommendation", "")
    else:
        itinerary["transit_to_next_city"] = None

    return itinerary


def get_category_breakdown(itinerary: dict) -> dict:
    """
    Totals up spending per category across all days.
    Used by the budget tracker in the Streamlit UI.

    Returns dict like:
        {"accommodation": 4800, "food": 2200, "transport": 800, ...}
    """
    breakdown = {
        "accommodation": 0.0,
        "food":          0.0,
        "transport":     0.0,
        "activity":      0.0,
        "free":          0.0,
    }

    for day_obj in itinerary.get("days_plan", []):
        for activity in day_obj.get("activities", []):
            category = activity.get("category", "activity").lower()
            cost     = float(activity.get("cost", 0))

            if category in breakdown:
                breakdown[category] += cost
            else:
                breakdown["activity"] += cost   # catch-all for unknown categories

    # Round all values
    return {k: round(v, 2) for k, v in breakdown.items()}


def get_all_coordinates(itinerary: dict) -> list[dict]:
    """
    Extracts a flat list of activities that have coordinates attached.
    Used by map_builder to place pins.

    Returns list of dicts with keys: name, lat, lng, day, cost, tip
    """
    coords = []
    for day_obj in itinerary.get("days_plan", []):
        for activity in day_obj.get("activities", []):
            if "lat" in activity and "lng" in activity:
                coords.append({
                    "name": activity.get("name", "Stop"),
                    "lat":  activity["lat"],
                    "lng":  activity["lng"],
                    "day":  day_obj.get("day", 1),
                    "cost": activity.get("cost", 0),
                    "tip":  activity.get("tip", ""),
                })
    return coords


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from budget_allocator import allocate_budget
    from geocoder import get_coordinates
    from prompt_builder import build_prompt
    from llm_client import call_llm
    import json

    print("=" * 55)
    print("LIVE TEST — full pipeline including parser")
    print("=" * 55)

    allocation  = allocate_budget(total_budget=12000, num_days=3, group_size=4)
    coordinates = get_coordinates("Goa, India")
    prompt      = build_prompt(
        city="Goa", days=3, group_size=4,
        month="December", travel_style="Adventure",
        allocation=allocation, coordinates=coordinates,
    )

    raw_itinerary       = call_llm(prompt)
    validated_itinerary = validate_itinerary(raw_itinerary, total_budget=12000)
    breakdown           = get_category_breakdown(validated_itinerary)

    print("\nValidated itinerary:")
    print(json.dumps(validated_itinerary, indent=2, ensure_ascii=False))

    print("\nCategory breakdown:")
    s = DEFAULT_CURRENCY_SIGN
    for category, amount in breakdown.items():
        print(f"  {category:<15} {s}{amount:,.0f}")