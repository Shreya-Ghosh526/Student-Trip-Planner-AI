from config import BUDGET_RATIOS, DEFAULT_CURRENCY_SIGN


def allocate_budget(total_budget: float, num_days: int, group_size: int) -> dict:
    """
    Split the total budget into per-category caps.

    Args:
        total_budget : total trip budget in INR (for the whole group)
        num_days     : number of days the trip lasts
        group_size   : number of people travelling

    Returns:
        dict with keys:
            total, per_person, per_day,
            accommodation, food, activities, transport,
            (and per_day breakdown for each category)
    """

    if total_budget <= 0:
        raise ValueError("Budget must be greater than 0")
    if num_days <= 0:
        raise ValueError("Number of days must be greater than 0")
    if group_size <= 0:
        raise ValueError("Group size must be at least 1")

    per_person = total_budget / group_size
    per_day    = total_budget / num_days

    # Apply ratios to get total cap per category for the whole trip
    accommodation = round(total_budget * BUDGET_RATIOS["accommodation"], 2)
    food          = round(total_budget * BUDGET_RATIOS["food"],          2)
    activities    = round(total_budget * BUDGET_RATIOS["activities"],    2)
    transport     = round(total_budget * BUDGET_RATIOS["transport"],     2)

    return {
        # ── Overall ──────────────────────────────────────────────────
        "total":               round(total_budget, 2),
        "per_person":          round(per_person, 2),
        "per_day":             round(per_day, 2),

        # ── Category totals (whole trip) ─────────────────────────────
        "accommodation":       accommodation,
        "food":                food,
        "activities":          activities,
        "transport":           transport,

        # ── Per-day breakdown (useful for prompt + UI display) ────────
        "accommodation_per_day": round(accommodation / num_days, 2),
        "food_per_day":          round(food          / num_days, 2),
        "activities_per_day":    round(activities    / num_days, 2),
        "transport_per_day":     round(transport     / num_days, 2),
    }


def allocate_multi_city(
    total_budget: float,
    cities: list[str],
    days_per_city: list[int],
    group_size: int,
) -> list[dict]:
    """
    Split the total budget across multiple cities, proportional to days spent.

    Args:
        total_budget  : total trip budget in INR
        cities        : list of city names  e.g. ["Goa", "Mumbai"]
        days_per_city : days spent in each city e.g. [3, 2]
        group_size    : number of people

    Returns:
        list of dicts — one per city, each with full allocation breakdown
        plus a "city" and "days" key added for reference
    """

    if len(cities) != len(days_per_city):
        raise ValueError("cities and days_per_city must have the same length")

    total_days   = sum(days_per_city)
    allocations  = []

    for city, days in zip(cities, days_per_city):
        # Each city gets a share of the budget proportional to days spent there
        city_budget = round(total_budget * (days / total_days), 2)
        allocation  = allocate_budget(city_budget, days, group_size)

        # Tag with city name and days so the prompt builder knows which is which
        allocation["city"] = city
        allocation["days"] = days
        allocations.append(allocation)

    return allocations


def format_allocation(allocation: dict) -> str:
    """
    Return a human-readable summary of a single city's budget allocation.
    Used for printing during tests and for debug displays in the UI.
    """
    s = DEFAULT_CURRENCY_SIGN
    lines = [
        f"  Total budget   : {s}{allocation['total']:,.0f}",
        f"  Per person     : {s}{allocation['per_person']:,.0f}",
        f"  Per day        : {s}{allocation['per_day']:,.0f}",
        f"  Accommodation  : {s}{allocation['accommodation']:,.0f}  ({s}{allocation['accommodation_per_day']:,.0f}/day)",
        f"  Food           : {s}{allocation['food']:,.0f}  ({s}{allocation['food_per_day']:,.0f}/day)",
        f"  Activities     : {s}{allocation['activities']:,.0f}  ({s}{allocation['activities_per_day']:,.0f}/day)",
        f"  Transport      : {s}{allocation['transport']:,.0f}  ({s}{allocation['transport_per_day']:,.0f}/day)",
    ]
    return "\n".join(lines)


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":

    print("=" * 50)
    print("TEST 1: Single city — Goa, 3 days, group of 4, ₹12,000")
    print("=" * 50)
    result = allocate_budget(
        total_budget=12000,
        num_days=3,
        group_size=4,
    )
    print(format_allocation(result))

    print()
    print("=" * 50)
    print("TEST 2: Multi-city — Goa (3 days) + Mumbai (2 days), group of 2, ₹20,000")
    print("=" * 50)
    multi = allocate_multi_city(
        total_budget=20000,
        cities=["Goa", "Mumbai"],
        days_per_city=[3, 2],
        group_size=2,
    )
    for city_allocation in multi:
        print(f"\n  City: {city_allocation['city']} ({city_allocation['days']} days)")
        print(format_allocation(city_allocation))