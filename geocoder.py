import os
import json
import time
import urllib.parse
import requests

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geocoder_cache.json")


def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache: dict):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"[geocoder] Warning: Could not save cache: {e}")


# Global tracking to enforce rate limits
LAST_QUERY_TIME = 0.0


def get_coordinates(city: str) -> dict | None:
    """
    Convert a city name or landmark name to latitude, longitude, and display name.
    Uses a local JSON cache to prevent excessive Nominatim queries and rate limiting.

    Args:
        city: plain text city name or landmark name

    Returns:
        dict with keys: city, lat, lng, display_name
        None if the location could not be found
    """
    global LAST_QUERY_TIME
    if not city or not city.strip():
        return None

    query = city.strip()
    cache = load_cache()

    # Case-insensitive cache check
    query_lower = query.lower()
    for cached_key, cached_val in cache.items():
        if cached_key.lower() == query_lower:
            return cached_val

    # Enforce 1-second delay between queries only if needed
    now = time.time()
    elapsed = now - LAST_QUERY_TIME
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)
    LAST_QUERY_TIME = time.time()

    try:
        print(f"[geocoder] Requesting Nominatim for: '{query}'")

        if GEOPY_AVAILABLE:
            geolocator = Nominatim(user_agent="student_trip_planner_shreya_unique_v2")
            location = geolocator.geocode(query, timeout=10)

            if location is None:
                cache[query] = None
                save_cache(cache)
                return None

            result = {
                "city":         query,
                "lat":          round(location.latitude, 6),
                "lng":          round(location.longitude, 6),
                "display_name": location.address,
            }
        else:
            url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=1"
            headers = {"User-Agent": "student_trip_planner_shreya_unique_v2"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    cache[query] = None
                    save_cache(cache)
                    return None
                
                loc_data = data[0]
                result = {
                    "city":         query,
                    "lat":          round(float(loc_data["lat"]), 6),
                    "lng":          round(float(loc_data["lon"]), 6),
                    "display_name": loc_data.get("display_name", query),
                }
            else:
                print(f"[geocoder] HTTP request failed: status code {response.status_code}")
                return None

        # Cache result
        cache[query] = result
        save_cache(cache)
        return result

    except Exception as e:
        print(f"[geocoder] Error resolving location for query '{query}': {e}")
        return None


def get_coordinates_multi(cities: list[str]) -> list[dict]:
    """
    Geocode multiple cities in sequence.

    Args:
        cities: list of city name strings

    Returns:
        list of dicts (same shape as get_coordinates).
        Cities that fail geocoding are skipped with a warning.
    """
    results = []

    for city in cities:
        coords = get_coordinates(city)
        if coords:
            results.append(coords)
        else:
            print(f"[geocoder] Warning: could not geocode '{city}' — skipping")

    return results


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_cities = ["Goa, India", "Manali, India", "Jaipur, India"]

    print("Testing geocoder with cache...\n")
    for city in test_cities:
        start_time = time.time()
        result = get_coordinates(city)
        elapsed = time.time() - start_time
        if result:
            print(f"  {result['city']} (took {elapsed:.2f}s)")
            print(f"    lat : {result['lat']}")
            print(f"    lng : {result['lng']}")
            print()
        else:
            print(f"  FAILED: {city}\n")
