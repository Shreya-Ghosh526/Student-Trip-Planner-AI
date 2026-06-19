import folium
import urllib.parse
from config import MAP_DEFAULT_ZOOM, MAP_TILE, ROUTE_COLOR, MARKER_COLOR, DEFAULT_CURRENCY_SIGN


def build_single_city_map(itinerary: dict, coordinates: dict) -> folium.Map:
    """
    Build a Folium map for a single city trip.
    Places a numbered marker for each activity and draws a route line across the day.

    Args:
        itinerary   : validated itinerary dict from parser.py
        coordinates : dict with lat/lng from geocoder.py

    Returns:
        folium.Map object ready to be rendered in Streamlit
    """

    # Centre the map on the city
    city_map = folium.Map(
        location=[coordinates["lat"], coordinates["lng"]],
        zoom_start=MAP_DEFAULT_ZOOM,
        tiles=MAP_TILE,
    )

    # Colour per day — cycles through if more than 6 days
    day_colors = ["#534AB7", "#5DCAA5", "#E07B5A", "#F5C842", "#7B9FE0", "#C45AB7"]

    for day_obj in itinerary.get("days_plan", []):
        day_num    = day_obj.get("day", 1)
        color      = day_colors[(day_num - 1) % len(day_colors)]
        day_coords = []   # collect coords for the route line

        for i, activity in enumerate(day_obj.get("activities", []), start=1):

            # Skip activities without coordinates
            if "lat" not in activity or "lng" not in activity:
                continue

            lat  = activity["lat"]
            lng  = activity["lng"]
            name = activity.get("name", "Stop")
            cost = activity.get("cost", 0)
            tip  = activity.get("tip", "")
            time = activity.get("time", "")

            day_coords.append([lat, lng])

            # Build Google Maps navigation link
            city_name = itinerary.get("city", "")
            gmaps_query = urllib.parse.quote_plus(f"{name}, {city_name}, India")
            gmaps_url = f"https://www.google.com/maps/search/?api=1&query={gmaps_query}"

            # Build popup HTML
            popup_html = f"""
            <div style="font-family: sans-serif; min-width: 180px;">
                <b style="color:{color};">Day {day_num} · Stop {i}</b><br>
                <b><a href="{gmaps_url}" target="_blank" style="text-decoration:none; color:#534AB7;">🗺️ {name}</a></b><br>
                <span style="color:#888;">🕐 {time}</span><br>
                <span style="color:#2a9d8f;">💰 {DEFAULT_CURRENCY_SIGN}{cost:,.0f}</span><br>
                <hr style="margin:4px 0;">
                <span style="font-size:12px;">💡 {tip}</span><br>
                <a href="{gmaps_url}" target="_blank" style="font-size:11px; color:#534AB7; font-weight:bold;">📍 Open Directions</a>
            </div>
            """

            folium.Marker(
                location=[lat, lng],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"Day {day_num}: {name}",
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                        background:{color};
                        color:white;
                        border-radius:50%;
                        width:28px; height:28px;
                        display:flex; align-items:center; justify-content:center;
                        font-weight:bold; font-size:13px;
                        border: 2px solid white;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    ">{i}</div>
                    """,
                    icon_size=(28, 28),
                    icon_anchor=(14, 14),
                ),
            ).add_to(city_map)

        # Draw route line connecting stops for this day
        if len(day_coords) > 1:
            folium.PolyLine(
                locations=day_coords,
                color=color,
                weight=3,
                opacity=0.7,
                tooltip=f"Day {day_num} route",
                dash_array="6 4",
            ).add_to(city_map)

    return city_map


def build_multi_city_map(
    itineraries: list[dict],
    coordinates_list: list[dict],
) -> folium.Map:
    """
    Build a single Folium map covering all cities in a multi-city trip.
    Each city gets its own colour. An inter-city line connects city centres.

    Args:
        itineraries      : list of validated itinerary dicts, one per city
        coordinates_list : list of coordinate dicts, one per city

    Returns:
        folium.Map object
    """

    if not coordinates_list:
        # Fallback to India centre if no coordinates
        return folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles=MAP_TILE)

    # Centre map on the midpoint of all cities
    avg_lat = sum(c["lat"] for c in coordinates_list) / len(coordinates_list)
    avg_lng = sum(c["lng"] for c in coordinates_list) / len(coordinates_list)

    multi_map = folium.Map(
        location=[avg_lat, avg_lng],
        zoom_start=6,
        tiles=MAP_TILE,
    )

    city_colors = ["#534AB7", "#5DCAA5", "#E07B5A", "#F5C842", "#7B9FE0"]
    city_centers = []

    for idx, (itinerary, coords) in enumerate(zip(itineraries, coordinates_list)):
        color = city_colors[idx % len(city_colors)]
        city_centers.append([coords["lat"], coords["lng"]])

        # City centre marker
        folium.Marker(
            location=[coords["lat"], coords["lng"]],
            tooltip=coords["city"],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    background:{color};
                    color:white;
                    border-radius:6px;
                    padding: 3px 8px;
                    font-weight:bold;
                    font-size:12px;
                    border: 2px solid white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    white-space:nowrap;
                ">{coords['city']}</div>
                """,
                icon_size=(100, 28),
                icon_anchor=(50, 14),
            ),
        ).add_to(multi_map)

        # Add activity markers for this city
        for day_obj in itinerary.get("days_plan", []):
            for i, activity in enumerate(day_obj.get("activities", []), start=1):
                if "lat" not in activity or "lng" not in activity:
                    continue

                # Build Google Maps navigation link
                city_name = coords.get("city", "")
                gmaps_query = urllib.parse.quote_plus(f"{activity.get('name', 'Stop')}, {city_name}, India")
                gmaps_url = f"https://www.google.com/maps/search/?api=1&query={gmaps_query}"

                popup_html = f"""
                <div style="font-family: sans-serif; min-width: 180px;">
                    <b style="color:{color};">{coords['city']} · Day {day_obj['day']}</b><br>
                    <b><a href="{gmaps_url}" target="_blank" style="text-decoration:none; color:#534AB7;">🗺️ {activity.get('name', 'Stop')}</a></b><br>
                    <span style="color:#2a9d8f;">💰 {DEFAULT_CURRENCY_SIGN}{activity.get('cost', 0):,.0f}</span><br>
                    <span style="font-size:12px;">💡 {activity.get('tip', '')}</span><br>
                    <a href="{gmaps_url}" target="_blank" style="font-size:11px; color:#534AB7; font-weight:bold;">📍 Open Directions</a>
                </div>
                """

                folium.CircleMarker(
                    location=[activity["lat"], activity["lng"]],
                    radius=7,
                    color=color,
                    fill=True,
                    fill_opacity=0.8,
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=activity.get("name", "Stop"),
                ).add_to(multi_map)

    # Draw inter-city route line
    if len(city_centers) > 1:
        folium.PolyLine(
            locations=city_centers,
            color=ROUTE_COLOR,
            weight=4,
            opacity=0.6,
            tooltip="Inter-city route",
            dash_array="10 6",
        ).add_to(multi_map)

    return multi_map


def get_map_html(fmap: folium.Map) -> str:
    """
    Convert a Folium map to an HTML string.
    Used by Streamlit to render the map via st.components.html()
    as a fallback if streamlit-folium has issues.
    """
    return fmap._repr_html_()


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from budget_allocator import allocate_budget
    from geocoder import get_coordinates
    from prompt_builder import build_prompt
    from llm_client import call_llm
    from parser import validate_itinerary
    import os

    print("=" * 55)
    print("LIVE TEST — building Folium map")
    print("=" * 55)

    allocation  = allocate_budget(total_budget=12000, num_days=3, group_size=4)
    coordinates = get_coordinates("Goa, India")
    prompt      = build_prompt(
        city="Goa", days=3, group_size=4,
        month="December", travel_style="Adventure",
        allocation=allocation, coordinates=coordinates,
    )

    raw          = call_llm(prompt)
    itinerary    = validate_itinerary(raw, total_budget=12000)
    city_map     = build_single_city_map(itinerary, coordinates)

    # Save to HTML file so you can open it in a browser
    output_path = "test_map.html"
    city_map.save(output_path)
    print(f"\nMap saved to: {os.path.abspath(output_path)}")
    print("Open test_map.html in your browser to see the map!")