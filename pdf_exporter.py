from fpdf import FPDF
import io
import urllib.parse
from config import DEFAULT_CURRENCY_SIGN


class ItineraryPDF(FPDF):
    """Custom FPDF class with header and footer."""

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(83, 74, 183)   # purple
        self.cell(0, 10, "Student Trip Planner", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(83, 74, 183)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def clean_pdf_text(text: str) -> str:
    """Helper to clean string of non-latin-1 characters to avoid FPDF encoding crashes."""
    if not text:
        return ""
    # Replace common characters that fail latin-1 encoding
    text = text.replace("•", "-").replace("₹", "Rs.").replace("—", "-").replace("–", "-")
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    return text.encode("latin-1", errors="ignore").decode("latin-1")


def generate_pdf(
    itinerary: dict,
    allocation: dict,
    breakdown: dict,
) -> bytes:
    """
    Generate a downloadable PDF itinerary.

    Args:
        itinerary  : validated itinerary dict from parser.py
        allocation : budget allocation dict from budget_allocator.py
        breakdown  : category spending dict from parser.get_category_breakdown()

    Returns:
        PDF as bytes — ready for Streamlit's st.download_button()
    """

    pdf = ItineraryPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    s = "Rs." 

    # ── Trip title ────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(40, 40, 40)
    city        = clean_pdf_text(itinerary.get("city", "Trip"))
    days        = itinerary.get("days", 0)
    group_size  = itinerary.get("group_size", 1)
    style       = clean_pdf_text(itinerary.get("travel_style", ""))

    pdf.cell(0, 12, f"{city} - {days} Day Itinerary", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, f"{style}  |  Group of {group_size}  |  Budget: {s}{allocation['total']:,.0f}",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # ── Budget summary box ────────────────────────────────────────────────────
    pdf.set_fill_color(245, 245, 255)
    pdf.set_draw_color(83, 74, 183)
    pdf.set_line_width(0.3)
    pdf.rect(10, pdf.get_y(), 190, 36, style="FD")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(83, 74, 183)
    pdf.cell(0, 7, "Budget Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)

    col_w = 47
    pdf.cell(col_w, 6, f"Total: {s}{allocation['total']:,.0f}")
    pdf.cell(col_w, 6, f"Per person: {s}{allocation['per_person']:,.0f}")
    pdf.cell(col_w, 6, f"Used: {s}{itinerary.get('grand_total', 0):,.0f}")
    pdf.cell(col_w, 6, f"Saved: {s}{allocation['total'] - itinerary.get('grand_total', 0):,.0f}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # ── Category breakdown ────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(83, 74, 183)
    pdf.cell(0, 7, "Spending by Category", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)

    category_icons = {
        "accommodation": "Stay",
        "food":          "Food",
        "transport":     "Transport",
        "activity":      "Activities",
        "free":          "Free",
    }

    for cat, amount in breakdown.items():
        if amount > 0:
            label = category_icons.get(cat, cat.title())
            pdf.cell(60, 6, f"  {label}:")
            pdf.cell(40, 6, f"{s}{amount:,.0f}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # ── Day by day plan ───────────────────────────────────────────────────────
    for day_obj in itinerary.get("days_plan", []):
        day_num = day_obj.get("day", "?")
        theme   = clean_pdf_text(day_obj.get("theme", ""))
        day_total = day_obj.get("day_total", 0)

        # Day header
        pdf.set_fill_color(83, 74, 183)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f"  Day {day_num} - {theme} | Total: {s}{day_total:,.0f}",
                 fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        # Activities
        for activity in day_obj.get("activities", []):
            name     = clean_pdf_text(activity.get("name", "Activity"))
            time     = clean_pdf_text(activity.get("time", ""))
            cost     = activity.get("cost", 0)
            category = clean_pdf_text(activity.get("category", "").title())
            tip      = clean_pdf_text(activity.get("tip", ""))

            # Build Google Maps URL for links in the PDF
            gmaps_query = urllib.parse.quote_plus(f"{name}, {city}, India")
            gmaps_url = f"https://www.google.com/maps/search/?api=1&query={gmaps_query}"

            # Print timing
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.cell(pdf.get_string_width(f"  {time} - "), 6, f"  {time} - ")

            # Print location name as a clickable link
            pdf.set_text_color(83, 74, 183)  # Use purple for links
            pdf.cell(pdf.get_string_width(name), 6, name, link=gmaps_url)

            # Print category and cost
            pdf.set_text_color(40, 40, 40)
            pdf.cell(0, 6, f" [{category}] {s}{cost:,.0f}", new_x="LMARGIN", new_y="NEXT")

            if tip:
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 5, f"     Tip: {tip}", new_x="LMARGIN", new_y="NEXT")

            pdf.ln(1)

        pdf.ln(4)

    # ── Budget Upgrades / Alternatives ────────────────────────────────────────
    upgrades = itinerary.get("budget_upgrades", [])
    if upgrades:
        pdf.set_fill_color(240, 238, 255)
        pdf.set_text_color(83, 74, 183)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "  Recommended Upgrades (If you can increase your budget)", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

        for item in upgrades:
            item_name = clean_pdf_text(item.get("name", ""))
            cost_val = item.get("extra_cost", 0)
            desc = clean_pdf_text(item.get("description", ""))

            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.cell(0, 6, f"  - {item_name} (Extra: {s}{cost_val:,.0f})", new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 5, f"    {desc}")
            pdf.ln(2)
        pdf.ln(3)

    # ── Savings tip ───────────────────────────────────────────────────────────
    savings_tip = clean_pdf_text(itinerary.get("savings_tip", ""))
    if savings_tip:
        pdf.set_fill_color(93, 202, 165)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "  Money Saving Tip", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.multi_cell(0, 6, f"  {savings_tip}")

    # Return PDF as bytes
    return bytes(pdf.output())


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from budget_allocator import allocate_budget
    from geocoder import get_coordinates
    from prompt_builder import build_prompt
    from llm_client import call_llm
    from parser import validate_itinerary, get_category_breakdown

    print("=" * 55)
    print("LIVE TEST — generating PDF itinerary")
    print("=" * 55)

    allocation  = allocate_budget(total_budget=12000, num_days=3, group_size=4)
    coordinates = get_coordinates("Goa, India")
    prompt      = build_prompt(
        city="Goa", days=3, group_size=4,
        month="December", travel_style="Adventure",
        allocation=allocation, coordinates=coordinates,
    )

    raw       = call_llm(prompt)
    itinerary = validate_itinerary(raw, total_budget=12000)
    breakdown = get_category_breakdown(itinerary)

    pdf_bytes = generate_pdf(itinerary, allocation, breakdown)

    with open("test_itinerary.pdf", "wb") as f:
        f.write(pdf_bytes)

    print("PDF saved to: test_itinerary.pdf")
    print("Open it to see the full itinerary!")