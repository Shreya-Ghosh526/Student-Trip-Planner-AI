import os
from dotenv import load_dotenv

# Load .env file so ANTHROPIC_API_KEY is available via os.getenv()
load_dotenv()

# ── API ──────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = "llama-3.3-70b-versatile"
MAX_TOKENS   = 4096
# ── BUDGET ALLOCATION RATIOS ─────────────────────────────────────────────────
# These decide how the total budget is split across categories.
# Must add up to 1.0 exactly.
BUDGET_RATIOS = {
    "accommodation": 0.40,   # 40% → stay (hostels, guesthouses)
    "food":          0.25,   # 25% → meals and drinks
    "activities":    0.20,   # 20% → sightseeing, entry fees, experiences
    "transport":     0.15,   # 15% → local travel (autos, buses, trains)
}

# ── TRAVEL STYLES ────────────────────────────────────────────────────────────
# Shown as options in the Streamlit form.
# The selected style gets injected into the prompt to personalise suggestions.
TRAVEL_STYLES = [
    "Adventure",
    "Beach & Relaxation",
    "Culture & Heritage",
    "Foodie",
    "Nature & Trekking",
    "Budget Backpacker",
]

# ── TRAVEL MONTHS ────────────────────────────────────────────────────────────
MONTHS = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December",
]

# ── APP DEFAULTS ─────────────────────────────────────────────────────────────
DEFAULT_CURRENCY      = "INR"      # currency symbol shown in the UI
DEFAULT_CURRENCY_SIGN = "₹"        # used in formatted strings
MAX_CITIES            = 5          # maximum cities allowed in multi-city mode
MAX_DAYS              = 15         # maximum trip duration
MAX_GROUP_SIZE        = 20         # maximum group size
LLM_RETRY_ATTEMPTS    = 2          # how many times to retry if LLM returns bad JSON

# ── MAP DEFAULTS ─────────────────────────────────────────────────────────────
MAP_DEFAULT_ZOOM  = 12             # folium map zoom level (12 = city level)
MAP_TILE          = "CartoDB DarkMatter"
ROUTE_COLOR       = "#06b6d4"      # neon teal line connecting stops on the map
MARKER_COLOR      = "#a855f7"      # vibrant purple pins for each activity location