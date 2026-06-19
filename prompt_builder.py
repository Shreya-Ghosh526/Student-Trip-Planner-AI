import json
import os
from config import DEFAULT_CURRENCY_SIGN


def load_city_data(city_name: str) -> dict | None:
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "city_data.json")
        if not os.path.exists(db_path):
            return None
        with open(db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
        
        # Clean city name (e.g. "Kolkata, India" -> "kolkata")
        target = city_name.strip().split(",")[0].strip().lower()
        
        # Match case-insensitively
        for key, val in db.items():
            if key.lower() == target:
                return val
        
        # Substring match (either way)
        for key, val in db.items():
            k_lower = key.lower()
            if target in k_lower or k_lower in target:
                return val
        return None
    except Exception as e:
        print(f"Error loading city data: {e}")
        return None


def build_prompt(
    city: str,
    days: int,
    group_size: int,
    month: str,
    travel_style: str,
    allocation: dict,
    coordinates: dict | None = None,
    next_city: str | None = None,
) -> str:
    """
    Assemble the full prompt for a single-city itinerary.

    Args:
        city         : destination city name
        days         : number of days
        group_size   : number of travellers
        month        : travel month e.g. "December"
        travel_style : e.g. "Adventure", "Foodie"
        allocation   : output of allocate_budget()
        coordinates  : output of get_coordinates() — optional, adds location context
        next_city    : next city name in multi-city leg — optional, adds transit instructions

    Returns:
        Complete prompt string ready to send to Claude
    """

    s = DEFAULT_CURRENCY_SIGN

    # Group label — makes the prompt more natural
    group_label = "solo traveller" if group_size == 1 else f"group of {group_size} students"

    # Location context — only added if geocoding succeeded
    location_context = ""
    if coordinates:
        location_context = f"""
LOCATION CONTEXT:
- Coordinates : {coordinates['lat']}, {coordinates['lng']}
- Full address : {coordinates['display_name'][:80]}
- Use these coordinates to suggest real, existing places in and around {city}.
"""

    # Load local database information
    city_data = load_city_data(city)
    db_context = ""
    seasonal_instruction = ""
    
    if city_data:
        must_visit_str = ", ".join(city_data.get("must_visit", []))
        entry_fees_str = json.dumps(city_data.get("entry_fees", {}), indent=2)
        stays_str = json.dumps(city_data.get("budget_stays", {}), indent=2)
        food_str = json.dumps(city_data.get("food", {}), indent=2)
        transport_str = json.dumps(city_data.get("local_transport", {}), indent=2)
        avoid_months = city_data.get("avoid_months", [])
        month_notes = city_data.get("seasonal_notes", {}).get(month, "")
        
        db_context = f"""
VERIFIED CITY DATABASE CONTEXT (You MUST prioritize these places, stays, dhabas, transport options and use these exact prices if they match the itinerary activities):
- Must Visit Landmarks: {must_visit_str}
- Landmark Entry Fees: {entry_fees_str}
- Budget Hostels/Stays: {stays_str}
- Budget Food/Dhabas (with meal prices): {food_str}
- Local Transport Options & Fares: {transport_str}
"""
        
        if month in avoid_months or month in ["April", "May", "June"]:
            seasonal_instruction = f"""
STRICT SEASONAL WEATHER AND TEMPERATURE SAFETY DIRECTIVE:
- Travel Month: {month}
- Seasonal note for {city} in {month}: "{month_notes}"
- Crucial Rule: The temperature/humidity during {month} in {city} is extreme. Do NOT suggest outdoor locations (like parks, open beaches, lakes, open-air ghats, or non-shaded monuments like Eco Park or Princep Ghat) during peak midday hours (10:00 AM to 5:00 PM).
- For the daytime (10:00 AM to 5:00 PM), suggest only air-conditioned indoor activities (e.g. museums, galleries, planetariums, indoor markets, libraries, or indoor dining).
- Schedule any outdoor visits strictly in the early morning (6:00 AM to 9:30 AM) or late evening (after 6:00 PM) when conditions are safe and comfortable.
"""
        else:
            seasonal_instruction = f"""
SEASONAL WEATHER CONTEXT (Travel Month: {month}):
- Seasonal note for {city} in {month}: "{month_notes}"
- Align activities to be weather-appropriate for {month}.
"""

    transit_instruction = ""
    transit_schema = ""
    if next_city:
        transit_instruction = f"\n10. Transit: Provide transport options (flights, trains, buses) and cost estimations from {city} to {next_city} for the group."
        transit_schema = f""",
  "transit_to_next_city": {{
    "next_city": "{next_city}",
    "flight_cost_estimation": "approximate flight cost range for the group e.g. Rs.6000-8000",
    "train_cost_estimation": "approximate train cost range for the group e.g. Rs.1500-2500 (Sleeper/3AC)",
    "alternative_cost_estimation": "approximate alternative cost (bus/shared cab) range for the group e.g. Rs.800-1200",
    "recommendation": "recommendation for students (e.g. Train is recommended to save money and enjoy the scenic route)"
  }}"""

    prompt = f"""You are an expert budget travel planner specialising in student-friendly trips across India.
Your job is to create a realistic, affordable, day-by-day itinerary that stays strictly within the given budget.
Always prioritise value for money. Never suggest luxury options.
{db_context}
{seasonal_instruction}

TRIP DETAILS:
- Destination   : {city}
- Duration      : {days} days
- Travel month  : {month}
- Group         : {group_label}
- Travel style  : {travel_style}
{location_context}
BUDGET CAPS (strict — do NOT exceed these):
- Total budget        : {s}{allocation['total']:,.0f}  ({s}{allocation['per_person']:,.0f} per person)
- Accommodation cap   : {s}{allocation['accommodation']:,.0f}  ({s}{allocation['accommodation_per_day']:,.0f} per night)
- Food cap            : {s}{allocation['food']:,.0f}  ({s}{allocation['food_per_day']:,.0f} per day)
- Activities cap      : {s}{allocation['activities']:,.0f}  ({s}{allocation['activities_per_day']:,.0f} per day)
- Transport cap       : {s}{allocation['transport']:,.0f}  ({s}{allocation['transport_per_day']:,.0f} per day)

RULES:
1. Every suggested cost must be realistic for {month} in {city}.
2. Accommodation: suggest hostels, Zostels, or guesthouses only — no hotels above {s}{allocation['accommodation_per_day']:,.0f} per night for the group.
3. Food: suggest local dhabas, street food, and markets — avoid sit-down restaurants unless very cheap. Prioritize the specific budget dhabas/restaurants listed in the database context, showing their specific cost estimation (like Lunch/Dinner).
4. Include at least one FREE activity per day (parks, beaches, temples, markets).
5. Transport: use local buses, autos, or shared cabs — no private taxis unless unavoidable.
6. Add a practical local tip for each activity.
7. The sum of all costs must NOT exceed {s}{allocation['total']:,.0f}.
8. Tailor suggestions to the travel style: {travel_style}.
9. Provide estimated latitude and longitude for each activity or landmark so they can be mapped with individual pins. Use realistic coordinates in or around {city} (close to actual landmarks).{transit_instruction}

OUTPUT INSTRUCTIONS:
- Return ONLY valid JSON. No explanation, no markdown, no extra text before or after.
- Use this exact schema:

{{
  "city": "{city}",
  "days": {days},
  "travel_style": "{travel_style}",
  "group_size": {group_size},
  "days_plan": [
    {{
      "day": 1,
      "theme": "one short theme for the day e.g. Beaches + Sunset",
      "activities": [
        {{
          "name": "activity or place name (exact name e.g. Victoria Memorial / Sharma Dhaba)",
          "time": "9:00 AM",
          "cost": 200,
          "category": "food | accommodation | transport | activity | free",
          "tip": "one practical local tip",
          "lat": 22.5448,
          "lng": 88.3426
        }}
      ],
      "day_total": 1200
    }}
  ],
  "grand_total": 11400,
  "budget_used_percent": 95.0,
  "savings_tip": "one overall money-saving tip for this trip",
  "budget_upgrades": [
    {{
      "name": "activity/stay upgrade name (e.g. Private Room at Zostel / Sunderbans Day Tour)",
      "extra_cost": 1500,
      "description": "Short explanation of what this upgrade is and why the student should consider increasing their budget for it."
    }}
  ]{transit_schema}
}}
"""
    return prompt.strip()


def build_multi_city_prompt(
    city: str,
    days: int,
    group_size: int,
    month: str,
    travel_style: str,
    allocation: dict,
    city_index: int,
    total_cities: int,
    coordinates: dict | None = None,
    next_city: str | None = None,
) -> str:
    """
    Builds prompt for one city in a multi-city trip.
    Adds context about which leg of the trip this is.
    Internally calls build_prompt and prepends multi-city context.
    """

    multi_context = f"NOTE: This is city {city_index} of {total_cities} in a multi-city trip. "
    multi_context += f"The student has {allocation['total']:,.0f} INR allocated specifically for {city}.\n\n"

    base_prompt = build_prompt(
        city=city,
        days=days,
        group_size=group_size,
        month=month,
        travel_style=travel_style,
        allocation=allocation,
        coordinates=coordinates,
        next_city=next_city,
    )

    return multi_context + base_prompt


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from budget_allocator import allocate_budget
    from geocoder import get_coordinates

    print("Building prompt for: Goa, 3 days, group of 4, ₹12,000, December, Adventure\n")

    allocation  = allocate_budget(total_budget=12000, num_days=3, group_size=4)
    coordinates = get_coordinates("Goa, India")

    prompt = build_prompt(
        city="Goa",
        days=3,
        group_size=4,
        month="December",
        travel_style="Adventure",
        allocation=allocation,
        coordinates=coordinates,
    )

    print(prompt)
    print(f"\n{'='*50}")
    print(f"Prompt length: {len(prompt)} characters / ~{len(prompt)//4} tokens")