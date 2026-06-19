# pyrefly: ignore [missing-import]
import streamlit as st
# pyrefly: ignore [missing-import]
from streamlit_folium import st_folium
import json

from config import (
    TRAVEL_STYLES, MONTHS, MAX_CITIES, MAX_DAYS,
    MAX_GROUP_SIZE, DEFAULT_CURRENCY_SIGN
)
from geocoder import get_coordinates, get_coordinates_multi
from budget_allocator import allocate_budget, allocate_multi_city
from prompt_builder import build_prompt, build_multi_city_prompt
from llm_client import call_llm, call_llm_multi_city, call_chat_llm
from parser import validate_itinerary, get_category_breakdown
from map_builder import build_single_city_map, build_multi_city_map
from pdf_exporter import generate_pdf

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Student Trip Planner",
    page_icon="🎒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background: radial-gradient(circle at 10% 20%, rgba(168, 85, 247, 0.12) 0%, rgba(0, 0, 0, 0) 50%),
                    radial-gradient(circle at 90% 80%, rgba(6, 182, 212, 0.12) 0%, rgba(0, 0, 0, 0) 50%),
                    #0b0b14 !important;
        background-attachment: fixed !important;
        color: #f3f4f6 !important;
    }

    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    .stApp {
        margin-left: 0px !important;
    }
    header {
        visibility: hidden !important;
    }
    footer {
        visibility: hidden !important;
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(22, 22, 37, 0.5) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    .glass-card:hover {
        border-color: rgba(168, 85, 247, 0.4) !important;
        box-shadow: 0 12px 40px 0 rgba(168, 85, 247, 0.15) !important;
        transform: translateY(-4px) !important;
    }

    .day-card {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-left: 5px solid #a855f7 !important;
        border-radius: 12px !important;
        padding: 1.2rem !important;
        margin-bottom: 1.2rem !important;
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15) !important;
        transition: all 0.2s ease !important;
    }

    .day-card:hover {
        border-color: rgba(168, 85, 247, 0.3) !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }

    /* Custom interactive buttons override */
    .stButton > button {
        background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.8rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.3) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100% !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(168, 85, 247, 0.5) !important;
        border: none !important;
        color: white !important;
    }

    .stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #e5e7eb !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: none !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
    }

    /* Input Fields Glass Styling */
    div[data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        color: white !important;
    }

    div[data-baseweb="select"] {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
    }

    /* Tab Overrides */
    button[data-baseweb="tab"] {
        color: #9ca3af !important;
        font-size: 1rem !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.3s !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #a855f7 !important;
        border-bottom: 2px solid #a855f7 !important;
        font-weight: 700 !important;
    }

    /* Metric Widgets Styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: #f3f4f6 !important;
    }

    .budget-box {
        background: rgba(139, 92, 246, 0.07) !important;
        border: 1px solid rgba(139, 92, 246, 0.15) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
    }

    .savings-tip {
        background: rgba(16, 185, 129, 0.08) !important;
        border-left: 4px solid #10b981 !important;
        border-radius: 12px !important;
        padding: 1rem 1.2rem !important;
        margin-top: 1.5rem !important;
        font-size: 0.95rem !important;
        color: #34d399 !important;
    }

    .category-badge {
        display: inline-block !important;
        padding: 3px 10px !important;
        border-radius: 20px !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        margin-left: 8px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    .activity-tip {
        font-size: 0.85rem !important;
        color: #a1a1aa !important;
        font-style: italic !important;
        margin-top: 0.2rem !important;
    }

    .main-title {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        background: linear-gradient(to right, #c084fc, #6366f1) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        text-align: center !important;
        margin-bottom: 0.2rem !important;
        letter-spacing: -1px !important;
    }

    .sub-title {
        font-size: 1.15rem !important;
        color: #9ca3af !important;
        text-align: center !important;
        margin-bottom: 2rem !important;
    }

    .hero-container {
        text-align: center !important;
        padding: 3.5rem 1.5rem !important;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(99, 102, 241, 0.05) 100%) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 24px !important;
        margin-bottom: 2.5rem !important;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3) !important;
    }

    .hero-title {
        font-size: 3.5rem !important;
        font-weight: 900 !important;
        background: linear-gradient(135deg, #c084fc 0%, #818cf8 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: -1.5px !important;
    }

    .hero-subtitle {
        font-size: 1.4rem !important;
        color: #d8b4fe !important;
        margin-bottom: 1.5rem !important;
    }

    .feature-card {
        background: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(8px) !important;
        padding: 1.8rem !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        transition: all 0.3s ease !important;
    }

    .feature-card:hover {
        transform: translateY(-5px) !important;
        border-color: rgba(168, 85, 247, 0.3) !important;
        background: rgba(255, 255, 255, 0.04) !important;
        box-shadow: 0 10px 30px rgba(168, 85, 247, 0.1) !important;
    }

    /* Style the native progress bar to be colorful */
    div[role="progressbar"] > div {
        background: linear-gradient(to right, #a855f7, #06b6d4) !important;
        border-radius: 6px !important;
    }

    /* --- FLOATING CHATBOT & TOGGLE BUTTON STYLE --- */
    
    /* Target the floating toggle button container */
    div.element-container:has(.floating-btn-anchor) + div.element-container {
        position: fixed !important;
        bottom: 25px !important;
        right: 25px !important;
        z-index: 999999 !important;
        width: auto !important;
        height: auto !important;
    }
    
    /* Target the button inside it */
    div.element-container:has(.floating-btn-anchor) + div.element-container button {
        width: 65px !important;
        height: 65px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%) !important;
        color: transparent !important; /* Hide original emoji or text */
        border: 2px solid rgba(255, 255, 255, 0.25) !important;
        box-shadow: 0 8px 30px rgba(168, 85, 247, 0.5) !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        padding: 0 !important;
        position: relative !important;
    }
    
    /* Hover effects for the floating action button */
    div.element-container:has(.floating-btn-anchor) + div.element-container button:hover {
        transform: scale(1.1) rotate(5deg) !important;
        box-shadow: 0 12px 35px rgba(168, 85, 247, 0.7) !important;
        border-color: rgba(255, 255, 255, 0.5) !important;
    }
    
    /* Hide the inner text label generated by Streamlit */
    div.element-container:has(.floating-btn-anchor) + div.element-container button p,
    div.element-container:has(.floating-btn-anchor) + div.element-container button div {
        display: none !important;
    }
    
    /* Add the cute robot face inside the button */
    div.element-container:has(.floating-btn-anchor) + div.element-container button::before {
        content: "🤖" !important;
        display: inline-block !important;
        font-size: 28px !important;
        color: white !important;
    }
    
    /* Add the small waving hand at the top-right */
    div.element-container:has(.floating-btn-anchor) + div.element-container button::after {
        content: "👋" !important;
        position: absolute !important;
        right: 8px !important;
        top: 8px !important;
        font-size: 18px !important;
        transform-origin: bottom right !important;
        transition: transform 0.3s ease !important;
    }
    
    /* Hover animation for the waving hand */
    @keyframes wave-hello {
        0% { transform: rotate(0deg); }
        15% { transform: rotate(25deg); }
        30% { transform: rotate(-15deg); }
        45% { transform: rotate(20deg); }
        60% { transform: rotate(-10deg); }
        75% { transform: rotate(15deg); }
        100% { transform: rotate(0deg); }
    }
    
    div.element-container:has(.floating-btn-anchor) + div.element-container button:hover::after {
        animation: wave-hello 1.2s ease-in-out infinite !important;
    }
    
    /* Target the floating chat window container */
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(.floating-chat-anchor) {
        position: fixed !important;
        bottom: 105px !important;
        right: 25px !important;
        width: 380px !important;
        max-height: 550px !important;
        background: #0d0e15 !important; /* Solid background to prevent text behind bleeding through */
        border: 1px solid rgba(168, 85, 247, 0.5) !important;
        border-radius: 20px !important;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7) !important;
        z-index: 999998 !important;
        padding: 18px 18px 10px 18px !important;
        display: flex !important;
        flex-direction: column !important;
        overflow: hidden !important;
        animation: slide-up-fade 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    
    @keyframes slide-up-fade {
        from {
            opacity: 0;
            transform: translateY(20px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    /* Custom close button styling */
    div.element-container:has(.close-btn-anchor) + div.element-container {
        display: flex !important;
        justify-content: flex-end !important;
        margin: 0 !important;
        padding: 0 !important;
        height: 0 !important; /* Collapse height to not push layout */
    }
    div.element-container:has(.close-btn-anchor) + div.element-container button {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: #f3f4f6 !important;
        font-size: 13px !important;
        cursor: pointer !important;
        width: 28px !important;
        height: 28px !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        transition: all 0.2s ease !important;
        position: absolute !important;
        top: -38px !important; /* Position correctly relative to header */
        right: 0px !important;
        z-index: 999999 !important;
    }
    div.element-container:has(.close-btn-anchor) + div.element-container button:hover {
        background: rgba(239, 68, 68, 0.4) !important;
        border-color: rgba(239, 68, 68, 0.6) !important;
        color: white !important;
        transform: rotate(90deg) !important;
    }
    
    /* Custom styling for the scroll area */
    .floating-chat-scroll::-webkit-scrollbar {
        width: 5px !important;
    }
    .floating-chat-scroll::-webkit-scrollbar-track {
        background: transparent !important;
    }
    .floating-chat-scroll::-webkit-scrollbar-thumb {
        background: rgba(168, 85, 247, 0.3) !important;
        border-radius: 10px !important;
    }
    .floating-chat-scroll::-webkit-scrollbar-thumb:hover {
        background: rgba(168, 85, 247, 0.5) !important;
    }

    /* Screen size layout responsiveness */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.2rem !important;
        }
        .hero-title {
            font-size: 2.5rem !important;
        }
        .hero-subtitle {
            font-size: 1.1rem !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
    }

    @media (max-width: 480px) {
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(.floating-chat-anchor) {
            bottom: 0px !important;
            right: 0px !important;
            width: 100% !important;
            height: 100% !important;
            max-height: 100% !important;
            border-radius: 0px !important;
            border: none !important;
            z-index: 999998 !important;
        }
        
        div.element-container:has(.floating-btn-anchor) + div.element-container {
            bottom: 15px !important;
            right: 15px !important;
        }
    }
</style>
""", unsafe_allow_html=True)


# ── Helper: category color ────────────────────────────────────────────────────
def category_color(cat: str) -> str:
    colors = {
        "accommodation": "#a855f7", # Violet
        "food":          "#f97316", # Orange
        "transport":     "#3b82f6", # Blue
        "activity":      "#06b6d4", # Neon Teal
        "free":          "#10b981", # Emerald
    }
    return colors.get(cat.lower(), "#8b5cf6")


# ── Dialog: Day Details Popup Modal ───────────────────────────────────────────
@st.dialog("📅 Day Details & Timeline")
def show_day_details_modal(day_obj: dict, city_name: str):
    s = DEFAULT_CURRENCY_SIGN
    import urllib.parse
    
    day_num   = day_obj.get("day", "?")
    theme     = day_obj.get("theme", "")
    day_total = day_obj.get("day_total", 0)
    
    st.markdown(f"### Day {day_num} Overview")
    st.markdown(f"#### *{theme}*")
    st.markdown(f"**💰 Day Budget Allocated:** {s}{day_total:,.0f}")
    st.write("---")
    
    for activity in day_obj.get("activities", []):
        name     = activity.get("name", "Activity")
        time     = activity.get("time", "")
        cost     = activity.get("cost", 0)
        category = activity.get("category", "activity")
        tip      = activity.get("tip", "")
        color    = category_color(category)

        # Build Google Maps URL for navigation
        gmaps_query = urllib.parse.quote_plus(f"{name}, {city_name}, India")
        gmaps_url = f"https://www.google.com/maps/search/?api=1&query={gmaps_query}"

        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-left: 4px solid {color}; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                <div>
                    <span style="font-weight: 800; font-size: 1.1rem; color: #f3f4f6; margin-right: 0.5rem;">⏰ {time}</span>
                    <a href="{gmaps_url}" target="_blank" style="text-decoration:none; color:#a855f7; font-weight:700; font-size:1.1rem;">🗺️ {name}</a>
                    <span class="category-badge" style="background:{color}22; color:{color}; border: 1px solid {color}33;">{category}</span>
                </div>
                <div style="font-weight: 800; font-size: 1.1rem; color: {color};">
                    {f"{s}{cost:,.0f}" if cost > 0 else "FREE"}
                </div>
            </div>
            {f'<div class="activity-tip" style="margin-top: 0.5rem; border-top: 1px dashed rgba(255,255,255,0.05); padding-top: 0.4rem;">💡 <b>Student Tip:</b> {tip}</div>' if tip else ''}
            <div style="margin-top: 0.5rem; text-align: right;">
                <a href="{gmaps_url}" target="_blank" style="font-size: 0.85rem; color: #a855f7; text-decoration: none; font-weight: 600;">📍 Open Directions in Maps →</a>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Dialog: Budget Upgrades & Savings Popup Modal ─────────────────────────────
@st.dialog("💡 Smart Recommendations & Upgrades")
def show_budget_upgrades_modal(itinerary: dict, allocation: dict):
    s = DEFAULT_CURRENCY_SIGN
    st.markdown("### 🎓 Student Savings & Upgrades Analysis")
    st.write("Review suggestions to optimize accommodations or add experiences based on student uniform discounts and group budget ratios.")
    
    savings_tip = itinerary.get("savings_tip", "")
    if savings_tip:
        st.markdown(f"""
        <div class="savings-tip" style="margin-top: 0px; margin-bottom: 1.5rem;">
            💡 <b>Student Discount Hack:</b> {savings_tip}
        </div>
        """, unsafe_allow_html=True)
        
    upgrades = itinerary.get("budget_upgrades", [])
    if upgrades:
        st.markdown("#### 🎒 Accommodation Upgrades & Alternatives")
        for item in upgrades:
            item_name = item.get("name", "")
            cost_val = item.get("extra_cost", 0)
            desc = item.get("description", "")
            
            st.markdown(f"""
            <div style="background: rgba(168, 85, 247, 0.05); border: 1px solid rgba(168, 85, 247, 0.15); border-radius: 10px; padding: 0.8rem 1rem; margin-bottom: 0.8rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                    <b style="color: #c084fc; font-size: 1rem;">✨ {item_name}</b>
                    <span style="font-weight: 700; color: #10b981;">+{s}{cost_val:,.0f}</span>
                </div>
                <span style="font-size: 0.9rem; color: #d1d5db;">{desc}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No premium upgrades suggested for this budget level. You are running a super-efficient trip! 🎒")


# ── Helper: render day cards grid ─────────────────────────────────────────────
def render_day_cards(itinerary: dict):
    s = DEFAULT_CURRENCY_SIGN
    city_name = itinerary.get("city", "")
    days_plan = itinerary.get("days_plan", [])
    
    st.markdown("### 📅 Select a Day to Explore Details")
    
    # Render in columns (3 columns max)
    cols = st.columns(3)
    for idx, day_obj in enumerate(days_plan):
        col = cols[idx % 3]
        day_num   = day_obj.get("day", "?")
        theme     = day_obj.get("theme", "")
        day_total = day_obj.get("day_total", 0)
        
        with col:
            st.markdown(f"""
            <div class="day-card" style="min-height: 140px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 0px;">
                <div>
                    <div style="display: flex; justify-content: space-between; font-weight: 800; color: #c084fc; font-size: 1.15rem; margin-bottom: 0.5rem;">
                        <span>Day {day_num}</span>
                        <span>{s}{day_total:,.0f}</span>
                    </div>
                    <div style="font-size: 0.95rem; font-weight: 500; color: #d1d5db; line-height: 1.35; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
                        {theme}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Button to open popup modal for day activities
            button_key = f"btn_explore_day_{city_name.replace(' ', '_')}_{day_num}_{idx}"
            if st.button(f"🔍 Explore Day {day_num}", key=button_key, use_container_width=True):
                show_day_details_modal(day_obj, city_name)
            
            st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)


# ── Helper: render budget tracker ─────────────────────────────────────────────
def render_budget_tracker(allocation: dict, breakdown: dict, grand_total: float, itinerary: dict, city_name: str):
    s = DEFAULT_CURRENCY_SIGN
    total   = allocation["total"]
    saved   = total - grand_total
    percent = round((grand_total / total) * 100, 1) if total > 0 else 0

    st.markdown("<div class='budget-box'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Budget",  f"{s}{total:,.0f}")
    col2.metric("Amount Used",   f"{s}{grand_total:,.0f}", f"{percent}%")
    col3.metric("Amount Saved",  f"{s}{saved:,.0f}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("**Spending by category:**")
    category_labels = {
        "accommodation": "Stay",
        "food":          "Food",
        "transport":     "Transport",
        "activity":      "Activities",
        "free":          "Free",
    }

    for cat, amount in breakdown.items():
        if amount > 0:
            cap   = allocation.get(cat, total)
            pct   = min(amount / cap, 1.0) if cap > 0 else 0
            label = category_labels.get(cat, cat.title())
            color = category_color(cat)
            st.markdown(f"**{label}** — {s}{amount:,.0f} / {s}{cap:,.0f}")
            st.progress(pct)
            
    st.write("---")
    # Button to open savings tips dialog popup
    btn_key = f"btn_budget_upgrades_{city_name.replace(' ', '_')}_{allocation['total']}"
    if st.button("💡 View Savings Tips & Budget Upgrades", key=btn_key, use_container_width=True):
        show_budget_upgrades_modal(itinerary, allocation)


def render_chatbot(city_name: str):
    st.markdown(f"### 🤖 TripBuddy Assistant for {city_name}")
    st.markdown("*Your cute, AI-powered companion for budget cafes, cheap food, free spots, and discounts!*")
    
    chat_key = f"chat_messages_{city_name.replace(' ', '_').lower()}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = [
            {
                "role": "system",
                "content": f"You are 'TripBuddy', a cute, friendly, and extremely helpful student travel assistant. Respond with a warm, enthusiastic tone using emojis. Help students find budget-friendly cafes, cheap dhabas, affordable restaurants, free sightseeing spots, and student discount hacks in {city_name}. Answer any doubts about their day plans. Always mention costs in Rupees (₹) where relevant."
            },
            {
                "role": "assistant",
                "content": f"Hey there! I'm TripBuddy, your travel assistant for **{city_name}**! 🎒 Ask me anything about cheap cafes, free sights, or how to save money during your days here! ☕🗺️"
            }
        ]
        
    # Render chat container with custom glassmorphism style
    st.markdown("<div class='glass-card' style='padding: 1rem; border-radius: 12px; margin-bottom: 1rem; max-height: 400px; overflow-y: auto;'>", unsafe_allow_html=True)
    for msg in st.session_state[chat_key]:
        if msg["role"] != "system":
            # Stylise bubble
            role_label = "🎒 You" if msg["role"] == "user" else "🤖 TripBuddy"
            bubble_color = "rgba(168, 85, 247, 0.1)" if msg["role"] == "user" else "rgba(6, 182, 212, 0.1)"
            border_color = "rgba(168, 85, 247, 0.3)" if msg["role"] == "user" else "rgba(6, 182, 212, 0.3)"
            
            st.markdown(f"""
            <div style="background: {bubble_color}; border: 1px solid {border_color}; border-radius: 10px; padding: 0.8rem 1rem; margin-bottom: 0.8rem; color: #f3f4f6;">
                <b style="font-size: 0.85rem; color: {'#c084fc' if msg['role']=='user' else '#22d3ee'}; text-transform: uppercase;">{role_label}</b>
                <div style="margin-top: 0.2rem; font-size: 0.95rem; line-height: 1.4;">{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Input
    user_query = st.chat_input("Ask TripBuddy about cafes, food, free spots, or uniform hacks...", key=f"chat_input_{city_name.replace(' ', '_').lower()}")
    if user_query:
        st.session_state[chat_key].append({"role": "user", "content": user_query})
        # Generate response
        with st.spinner("TripBuddy is thinking... ☕"):
            response = call_chat_llm(st.session_state[chat_key])
        st.session_state[chat_key].append({"role": "assistant", "content": response})
        st.rerun()


# Load cities list for selectbox
def get_db_cities():
    try:
        import os
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "city_data.json")
        if os.path.exists(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                return sorted(list(json.load(f).keys()))
    except Exception as e:
        print(f"Error loading cities: {e}")
    return []

db_cities = get_db_cities()


# Initialize start session state
if "started" not in st.session_state:
    st.session_state["started"] = False
if "edit_mode" not in st.session_state:
    st.session_state["edit_mode"] = True

generate_btn = False
city = ""
cities = []
days_per_city = []
total_budget = 12000
num_days = 3
group_size = 4
month = "December"
style = "Budget Backpacker"
trip_mode = "Single City"

# ── MAIN AREA ─────────────────────────────────────────────────────────────────
if not st.session_state["started"]:
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">🎒 Student Trip Planner</div>
        <div class="hero-subtitle">Smart AI-powered itineraries that respect your student budget</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("hero_travel_illustration.png", use_container_width=True)
        
    st.markdown("<h2 style='text-align: center; color: #c084fc; margin-top: 2rem; margin-bottom: 2rem; font-weight:800; letter-spacing:-0.5px;'>What makes us different? 🤔</h2>", unsafe_allow_html=True)
    
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("""
        <div class="feature-card">
            <h3 style="color:#c084fc; margin-top:0; font-size:1.25rem; font-weight:700;">💰 True Student Budgets</h3>
            <p style="color:#d1d5db; font-size:0.92rem; margin-bottom:0; line-height:1.45;">Smart ratio allocation splits your budget for stay, food, transport and entry fees, so you never run out of cash.</p>
        </div>
        """, unsafe_allow_html=True)
    with f2:
        st.markdown("""
        <div class="feature-card">
            <h3 style="color:#c084fc; margin-top:0; font-size:1.25rem; font-weight:700;">📍 Verified Local DB</h3>
            <p style="color:#d1d5db; font-size:0.92rem; margin-bottom:0; line-height:1.45;">Reads accurate, updated local databases (like student uniform discounts at Victoria Memorial & camera fees at Indian Museum).</p>
        </div>
        """, unsafe_allow_html=True)
    with f3:
        st.markdown("""
        <div class="feature-card">
            <h3 style="color:#c084fc; margin-top:0; font-size:1.25rem; font-weight:700;">🌡️ Weather-Safe Planning</h3>
            <p style="color:#d1d5db; font-size:0.92rem; margin-bottom:0; line-height:1.45;">Monitors extreme heat/monsoon and dynamically reschedules outdoor sights to morning/evening, suggesting indoor AC activities during peak hours.</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    f4, f5, f6 = st.columns(3)
    with f4:
        st.markdown("""
        <div class="feature-card">
            <h3 style="color:#c084fc; margin-top:0; font-size:1.25rem; font-weight:700;">🗺️ Instant Navigation</h3>
            <p style="color:#d1d5db; font-size:0.92rem; margin-bottom:0; line-height:1.45;">Every suggested dhaba, hostel, and monument includes a direct Google Maps link. Just click and navigate immediately.</p>
        </div>
        """, unsafe_allow_html=True)
    with f5:
        st.markdown("""
        <div class="feature-card">
            <h3 style="color:#c084fc; margin-top:0; font-size:1.25rem; font-weight:700;">🚄 Group Transit Costs</h3>
            <p style="color:#d1d5db; font-size:0.92rem; margin-bottom:0; line-height:1.45;">Multi-city modes estimate group flight, train (3AC/Sleeper), and bus fares so you can plan travel in advance.</p>
        </div>
        """, unsafe_allow_html=True)
    with f6:
        st.markdown("""
        <div class="feature-card">
            <h3 style="color:#c084fc; margin-top:0; font-size:1.25rem; font-weight:700;">📄 Sleek PDF Exports</h3>
            <p style="color:#d1d5db; font-size:0.92rem; margin-bottom:0; line-height:1.45;">Download complete beautiful summaries of daily itineraries, budget allocations, and custom money-saving tips as offline PDFs.</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_btn_1, col_btn_2, col_btn_3 = st.columns([1, 2, 1])
    with col_btn_2:
        if st.button("✨ Start Planning Your Trip", use_container_width=True, type="primary"):
            st.session_state["started"] = True
            st.rerun()

else:
    st.markdown("<div class='main-title'>🎒 Student Trip Planner</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>AI-powered budget itineraries for students</div>", unsafe_allow_html=True)

    # Check if we should display the input form
    if "mode" not in st.session_state or st.session_state.get("edit_mode", True):
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### 🎒 Configure Your Trip Details")
        
        trip_mode = st.radio(
            "Select Trip Mode",
            ["Single City", "Multi City"],
            horizontal=True,
            index=0 if st.session_state.get("user_trip_mode", "Single City") == "Single City" else 1
        )
        
        st.markdown("---")
        
        if trip_mode == "Single City":
            c1, c2 = st.columns(2)
            with c1:
                default_city = st.session_state.get("user_city", "Kolkata")
                default_idx = db_cities.index(default_city) if default_city in db_cities else 0
                selected_city = st.selectbox(
                    "Destination City",
                    options=db_cities + ["Other (Type custom city)"],
                    index=default_idx
                )
                if selected_city == "Other (Type custom city)":
                    city = st.text_input("Type Custom City", value="" if default_city in db_cities else default_city, placeholder="e.g. Kedarnath, Kasol")
                else:
                    city = selected_city
            with c2:
                num_days = st.slider("Number of Days", min_value=1, max_value=MAX_DAYS, value=st.session_state.get("user_num_days", 3))
        else:
            num_cities = st.slider("Number of Cities", min_value=2, max_value=MAX_CITIES, value=st.session_state.get("user_num_cities", 2))
            cities         = []
            days_per_city  = []

            for i in range(num_cities):
                st.markdown(f"**City {i+1}**")
                c1, c2 = st.columns([2, 1])
                with c1:
                    default_c = st.session_state.get("user_cities", [])[i] if "user_cities" in st.session_state and i < len(st.session_state["user_cities"]) else db_cities[i % len(db_cities)]
                    default_idx = db_cities.index(default_c) if default_c in db_cities else 0
                    sel_city = st.selectbox(
                        f"Select City {i+1}",
                        options=db_cities + ["Other (Type custom city)"],
                        index=default_idx,
                        key=f"sel_city_{i}"
                    )
                    if sel_city == "Other (Type custom city)":
                        city_name = st.text_input(f"Type City {i+1}", value="" if default_c in db_cities else default_c, key=f"city_{i}", placeholder="e.g. Patna")
                    else:
                        city_name = sel_city
                with c2:
                    default_d = st.session_state.get("user_days_per_city", [])[i] if "user_days_per_city" in st.session_state and i < len(st.session_state["user_days_per_city"]) else 2
                    city_days = st.number_input(f"Days", min_value=1, max_value=MAX_DAYS,
                                                value=default_d, key=f"days_{i}")
                cities.append(city_name)
                days_per_city.append(city_days)

        st.markdown("---")

        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        with col_c1:
            total_budget = st.number_input(
                f"Total Budget (INR)",
                min_value=500,
                max_value=500000,
                value=st.session_state.get("user_total_budget", 12000),
                step=500,
            )
        with col_c2:
            group_size = st.slider("Group Size", min_value=1, max_value=MAX_GROUP_SIZE, value=st.session_state.get("user_group_size", 4))
        with col_c3:
            default_m = st.session_state.get("user_month", "December")
            m_idx = MONTHS.index(default_m) if default_m in MONTHS else 11
            month = st.selectbox("Travel Month", MONTHS, index=m_idx)
        with col_c4:
            default_s = st.session_state.get("user_style", "Budget Backpacker")
            s_idx = TRAVEL_STYLES.index(default_s) if default_s in TRAVEL_STYLES else 0
            style = st.selectbox("Travel Style", TRAVEL_STYLES, index=s_idx)

        st.markdown("<br>", unsafe_allow_html=True)
        
        col_btn_1, col_btn_2 = st.columns([3, 1])
        with col_btn_1:
            generate_btn = st.button("✨ Generate Custom Student Itinerary", use_container_width=True, type="primary")
        with col_btn_2:
            if st.button("🏠 Back to Home", use_container_width=True):
                st.session_state["started"] = False
                for k in ["mode", "itinerary", "itineraries", "allocation", "allocations", "breakdown", "breakdowns", "city_map", "multi_map", "coordinates", "cities", "edit_mode", "user_total_budget", "user_group_size", "user_month", "user_style", "user_trip_mode", "user_city", "user_num_days", "user_num_cities", "user_cities", "user_days_per_city"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        if generate_btn:
            # Save inputs to session state
            st.session_state["user_total_budget"] = total_budget
            st.session_state["user_group_size"] = group_size
            st.session_state["user_month"] = month
            st.session_state["user_style"] = style
            st.session_state["user_trip_mode"] = trip_mode
            if trip_mode == "Single City":
                st.session_state["user_city"] = city
                st.session_state["user_num_days"] = num_days
            else:
                st.session_state["user_cities"] = cities
                st.session_state["user_days_per_city"] = days_per_city
                st.session_state["user_num_cities"] = num_cities

            # Validation
            if trip_mode == "Single City":
                if not city or not city.strip():
                    st.error("Please enter a destination city.")
                    st.stop()
            else:
                if any(not c or not c.strip() for c in cities):
                    st.error("Please fill in all city names.")
                    st.stop()

            with st.spinner("Planning your trip... this takes a few seconds ✈️"):
                try:
                    # ── SINGLE CITY ───────────────────────────────────────────────
                    if trip_mode == "Single City":
                        allocation  = allocate_budget(total_budget, num_days, group_size)
                        coordinates = get_coordinates(f"{city}, India")
                        prompt      = build_prompt(
                            city=city, days=num_days, group_size=group_size,
                            month=month, travel_style=style,
                            allocation=allocation, coordinates=coordinates,
                        )
                        raw_itinerary = call_llm(prompt)
                        itinerary     = validate_itinerary(raw_itinerary, total_budget)
                        breakdown     = get_category_breakdown(itinerary)
                        city_map      = build_single_city_map(itinerary, coordinates) if coordinates else None

                        st.session_state["itinerary"]   = itinerary
                        st.session_state["allocation"]  = allocation
                        st.session_state["breakdown"]   = breakdown
                        st.session_state["city_map"]    = city_map
                        st.session_state["mode"]        = "single"
                        st.session_state["coordinates"] = coordinates

                    # ── MULTI CITY ────────────────────────────────────────────────
                    else:
                        total_days      = sum(days_per_city)
                        allocations     = allocate_multi_city(total_budget, cities, days_per_city, group_size)
                        coordinates_list = get_coordinates_multi([f"{c}, India" for c in cities])
                        
                        prompts = []
                        for i, (city_name, days, alloc) in enumerate(zip(cities, days_per_city, allocations)):
                            coords = next((c for c in coordinates_list if c["city"].lower() == city_name.lower() or c["city"].startswith(city_name[:4])), None)
                            next_c = cities[i+1] if i < len(cities) - 1 else None
                            prompt = build_multi_city_prompt(
                                city=city_name, days=days, group_size=group_size,
                                month=month, travel_style=style,
                                allocation=alloc, city_index=i+1,
                                total_cities=len(cities), coordinates=coords,
                                next_city=next_c,
                            )
                            prompts.append(prompt)

                        raw_itineraries = call_llm_multi_city(prompts)
                        itineraries     = [validate_itinerary(r, a["total"])
                                           for r, a in zip(raw_itineraries, allocations)]
                        breakdowns      = [get_category_breakdown(it) for it in itineraries]
                        multi_map       = build_multi_city_map(itineraries, coordinates_list)

                        st.session_state["itineraries"]       = itineraries
                        st.session_state["allocations"]       = allocations
                        st.session_state["breakdowns"]        = breakdowns
                        st.session_state["multi_map"]         = multi_map
                        st.session_state["cities"]            = cities
                        st.session_state["mode"]              = "multi"

                    st.session_state["edit_mode"] = False
                    st.rerun()

                except Exception as e:
                    st.error(f"Something went wrong: {e}")
                    st.stop()

    else:
        # Load active parameters
        trip_mode = st.session_state.get("user_trip_mode", "Single City")
        total_budget = st.session_state.get("user_total_budget", 12000)
        group_size = st.session_state.get("user_group_size", 4)
        month = st.session_state.get("user_month", "December")
        style = st.session_state.get("user_style", "Budget Backpacker")
        
        if trip_mode == "Single City":
            city = st.session_state.get("user_city", "Kolkata")
        else:
            cities = st.session_state.get("user_cities", [])
            
        # Display summary card
        st.markdown(f"""
        <div class="glass-card" style="padding: 1.2rem 1.8rem; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <span style="font-size: 0.75rem; text-transform: uppercase; color: #c084fc; font-weight: 800; letter-spacing: 1.5px;">ACTIVE TRIP PARAMETERS</span>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #f3f4f6; margin-top: 0.3rem;">
                        📍 {" → ".join(cities) if trip_mode == 'Multi City' else city} 
                        &nbsp;·&nbsp; 👥 {group_size} students 
                        &nbsp;·&nbsp; 💰 ₹{total_budget:,.0f} 
                        &nbsp;·&nbsp; 📅 {month} 
                        &nbsp;·&nbsp; 🎒 {style}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_sum_1, col_sum_2, col_sum_3 = st.columns([4, 1, 1])
        with col_sum_2:
            if st.button("✏️ Modify Search", use_container_width=True):
                st.session_state["edit_mode"] = True
                st.rerun()
        with col_sum_3:
            if st.button("🏠 Back to Home", use_container_width=True, type="secondary"):
                st.session_state["started"] = False
                for k in ["mode", "itinerary", "itineraries", "allocation", "allocations", "breakdown", "breakdowns", "city_map", "multi_map", "coordinates", "cities", "edit_mode", "user_total_budget", "user_group_size", "user_month", "user_style", "user_trip_mode", "user_city", "user_num_days", "user_num_cities", "user_cities", "user_days_per_city"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()
        
        st.write("---")

        # DISPLAY RESULTS
        if st.session_state["mode"] == "single":
            itinerary   = st.session_state["itinerary"]
            allocation  = st.session_state["allocation"]
            breakdown   = st.session_state["breakdown"]
            city_map    = st.session_state["city_map"]
            grand_total = itinerary.get("grand_total", 0)

            st.success(f"Your {itinerary.get('days')} day itinerary for **{itinerary.get('city')}** is ready!")

            tab1, tab2, tab3, tab4 = st.tabs(["📅 Itinerary", "💰 Budget", "🗺️ Map", "💬 Ask TripBuddy AI"])

            with tab1:
                render_day_cards(itinerary)
                
                st.markdown("---")
                pdf_bytes = generate_pdf(itinerary, allocation, breakdown)
                st.download_button(
                    label="📄 Download PDF Itinerary",
                    data=pdf_bytes,
                    file_name=f"{itinerary.get('city', 'trip')}_itinerary.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            with tab2:
                render_budget_tracker(allocation, breakdown, grand_total, itinerary, itinerary.get("city", "city"))

            with tab3:
                if city_map:
                    st_folium(city_map, width=700, height=500, key="single_city_map", returned_objects=[])
                else:
                    st.warning("Map could not be generated for this city.")

            with tab4:
                render_chatbot(itinerary.get("city", "city"))

        elif st.session_state["mode"] == "multi":
            itineraries = st.session_state["itineraries"]
            allocations = st.session_state["allocations"]
            breakdowns  = st.session_state["breakdowns"]
            multi_map   = st.session_state["multi_map"]
            cities      = st.session_state["cities"]

            st.success(f"Multi-city itinerary ready for: **{' → '.join(cities)}**")

            # Map shown at top for multi city
            st.markdown("### 🗺️ Your Route")
            st_folium(multi_map, width=700, height=400, key="multi_city_map", returned_objects=[])

            # Tabs per city
            city_tabs = st.tabs([f"📍 {c}" for c in cities])

            for tab, itinerary, allocation, breakdown in zip(city_tabs, itineraries, allocations, breakdowns):
                with tab:
                    grand_total = itinerary.get("grand_total", 0)

                    inner_tab1, inner_tab2, inner_tab3 = st.tabs(["📅 Itinerary", "💰 Budget", "💬 Ask TripBuddy AI"])

                    with inner_tab1:
                        render_day_cards(itinerary)

                        # Transit recommendation if available
                        transit = itinerary.get("transit_to_next_city")
                        if transit and transit.get("next_city"):
                            next_city_name = transit.get("next_city")
                            st.markdown(f"### 🚀 Transit to {next_city_name}")
                            st.markdown(f"""
                            <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-left: 4px solid #06b6d4; border-radius: 12px; padding: 1.2rem; margin-bottom: 1.5rem;">
                                <p style="margin: 0 0 0.8rem 0; font-weight: 800; color: #06b6d4; font-size: 1.1rem;">Recommended Group Transit Options:</p>
                                <table style="width: 100%; border-collapse: collapse; font-size: 0.95rem; color: #f3f4f6;">
                                    <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
                                        <th style="text-align: left; padding: 8px 8px 8px 0; color: #a1a1aa; font-weight: 500;">✈️ Flight</th>
                                        <td style="padding: 8px 8px; font-weight: 700; color: #f3f4f6;">{transit.get('flight_cost_estimation', 'N/A')}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
                                        <th style="text-align: left; padding: 8px 8px 8px 0; color: #a1a1aa; font-weight: 500;">🛞 Train</th>
                                        <td style="padding: 8px 8px; font-weight: 700; color: #f3f4f6;">{transit.get('train_cost_estimation', 'N/A')}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
                                        <th style="text-align: left; padding: 8px 8px 8px 0; color: #a1a1aa; font-weight: 500;">🚌 Bus / Alternative</th>
                                        <td style="padding: 8px 8px; font-weight: 700; color: #f3f4f6;">{transit.get('alternative_cost_estimation', 'N/A')}</td>
                                    </tr>
                                </table>
                                <p style="margin: 1rem 0 0 0; font-size: 0.92rem; font-style: italic; color: #d1d5db; line-height: 1.4;">
                                    <b>💡 Advice:</b> {transit.get('recommendation', 'No recommendation provided.')}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)

                        st.markdown("---")
                        pdf_bytes = generate_pdf(itinerary, allocation, breakdown)
                        st.download_button(
                            label=f"📄 Download {itinerary.get('city')} PDF",
                            data=pdf_bytes,
                            file_name=f"{itinerary.get('city', 'trip')}_itinerary.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key=f"pdf_{itinerary.get('city')}",
                        )

                    with inner_tab2:
                        render_budget_tracker(allocation, breakdown, grand_total, itinerary, itinerary.get("city", "city"))

                    with inner_tab3:
                        render_chatbot(itinerary.get("city", "city"))


# ── Global Floating Chatbot ───────────────────────────────────────────────────
if "show_chat" not in st.session_state:
    st.session_state["show_chat"] = False

# Render the floating chat window if toggled ON
if st.session_state["show_chat"]:
    active_city = "India"
    if "mode" in st.session_state:
        if st.session_state["mode"] == "single" and "itinerary" in st.session_state:
            active_city = st.session_state["itinerary"].get("city", "India")
        elif st.session_state["mode"] == "multi" and "cities" in st.session_state and st.session_state["cities"]:
            active_city = st.session_state["cities"][0]
            
    chat_key = f"chat_messages_global_{active_city.replace(' ', '_').lower()}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = [
            {
                "role": "system",
                "content": f"You are 'TripBuddy', a cute, friendly, and extremely helpful student travel assistant. Respond with a warm, enthusiastic tone using emojis. Help students find budget-friendly cafes, cheap dhabas, affordable restaurants, free sightseeing spots, and student discount hacks in {active_city}. Answer any doubts about travel. Always mention costs in Rupees (₹) where relevant."
            },
            {
                "role": "assistant",
                "content": f"Hey there! I'm TripBuddy, your travel assistant for **{active_city}**! 🎒 Ask me anything about cheap cafes, free sights, or how to save money! ☕"
            }
        ]
        
    # Floating chat box container
    with st.container():
        st.markdown('<div class="floating-chat-anchor"></div>', unsafe_allow_html=True)
        
        # Header columns
        h_col1, h_col2 = st.columns([5, 1])
        with h_col1:
            st.markdown(f'<div style="display: flex; align-items: center; gap: 8px;"><span style="font-size: 22px;">🤖</span><div><b style="color: #c084fc; font-size: 1.05rem; display: block; line-height: 1.2;">TripBuddy AI</b><span style="font-size: 0.78rem; color: #22d3ee; font-weight: 500;">Assistant for {active_city}</span></div></div>', unsafe_allow_html=True)
        with h_col2:
            st.markdown('<div class="close-btn-anchor"></div>', unsafe_allow_html=True)
            if st.button("✖️", key="close_chat_btn", use_container_width=True):
                st.session_state["show_chat"] = False
                st.rerun()
                
        # Chat Messages List
        messages_html = ""
        for msg in st.session_state[chat_key]:
            if msg["role"] != "system":
                role_label = "🎒 You" if msg["role"] == "user" else "🤖 TripBuddy"
                bubble_color = "rgba(168, 85, 247, 0.08)" if msg["role"] == "user" else "rgba(6, 182, 212, 0.08)"
                border_color = "rgba(168, 85, 247, 0.25)" if msg["role"] == "user" else "rgba(6, 182, 212, 0.25)"
                margin_type = "margin-left: auto;" if msg["role"] == "user" else "margin-right: auto;"
                color_val = '#c084fc' if msg['role']=='user' else '#22d3ee'
                
                messages_html += f'<div style="background: {bubble_color}; border: 1px solid {border_color}; border-radius: 12px; padding: 0.8rem 1rem; margin-bottom: 0.8rem; color: #f3f4f6; max-width: 85%; {margin_type}">' \
                                 f'<b style="font-size: 0.72rem; color: {color_val}; text-transform: uppercase; letter-spacing: 0.5px;">{role_label}</b>' \
                                 f'<div style="margin-top: 0.2rem; font-size: 0.88rem; line-height: 1.4; text-align: left;">{msg["content"]}</div>' \
                                 f'</div>'
                
        st.markdown(f'<div class="floating-chat-scroll" style="height: 330px; overflow-y: auto; padding-right: 5px; margin-bottom: 12px; display: flex; flex-direction: column;">{messages_html}</div>'
                    f'<script>'
                    f'setTimeout(() => {{'
                    f'const scrollDivs = (document.querySelectorAll(".floating-chat-scroll").length > 0) ? document.querySelectorAll(".floating-chat-scroll") : window.parent.document.querySelectorAll(".floating-chat-scroll");'
                    f'scrollDivs.forEach(el => {{ el.scrollTop = el.scrollHeight; }});'
                    f'}}, 100);'
                    f'</script>', unsafe_allow_html=True)
        
        # User input field
        user_query = st.chat_input("Ask TripBuddy...", key="floating_chat_input")
        if user_query:
            st.session_state[chat_key].append({"role": "user", "content": user_query})
            with st.spinner("TripBuddy is thinking..."):
                response = call_chat_llm(st.session_state[chat_key])
            st.session_state[chat_key].append({"role": "assistant", "content": response})
            st.rerun()

# Floating toggle button always rendered
st.markdown('<div class="floating-btn-anchor"></div>', unsafe_allow_html=True)
if st.button("🤖", key="chat_toggle_btn"):
    st.session_state["show_chat"] = not st.session_state["show_chat"]
    st.rerun()