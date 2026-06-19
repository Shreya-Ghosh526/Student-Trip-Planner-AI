# 🎒 Student Trip Planner AI

AI-powered travel planning application that generates personalized, budget-friendly travel itineraries using Large Language Models (LLMs), interactive maps, and intelligent budget allocation.

## 🚀 Features

- 🤖 AI-generated day-wise travel itineraries
- 💰 Smart budget allocation for accommodation, food, transport, and activities
- 🗺️ Interactive maps using Folium and OpenStreetMap
- 📍 Automatic location geocoding
- 🏨 Budget-friendly accommodation recommendations
- 🍜 Local food and attraction suggestions
- 🌍 Multi-city trip planning support
- 📄 PDF itinerary export
- 🎯 Travel-style based recommendations
- 📅 Seasonal travel guidance

---

## 🛠️ Tech Stack

- Python
- Streamlit
- Groq (Llama 3.3 70B)
- Folium
- Geopy
- FPDF
- OpenStreetMap
- JSON
- Requests

---

## 📂 Project Structure

```text
Student-Trip-Planner-AI/
│
├── app.py
├── config.py
├── budget_allocator.py
├── geocoder.py
├── llm_client.py
├── parser.py
├── map_builder.py
├── pdf_exporter.py
├── prompt_builder.py
├── city_data.json
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/student-trip-planner-ai.git
cd student-trip-planner-ai
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

---

## ▶️ Run Application

```bash
streamlit run app.py
```

The application will open in your browser automatically.

---

## 📸 Key Functionalities

### Smart Itinerary Generation
Generate complete day-by-day travel plans based on:

- Destination
- Budget
- Group size
- Travel month
- Travel style

### Budget Optimization

Automatically distributes budget across:

- Accommodation
- Food
- Activities
- Transportation

### Interactive Mapping

- Attraction markers
- Travel routes
- Navigation support
- OpenStreetMap integration

### PDF Export

Download professionally formatted itineraries for offline use.

---

## 🌟 Future Improvements

- Hotel booking integration
- Flight recommendation system
- Real-time weather updates
- Expense tracking
- User authentication
- Trip sharing and collaboration

---

## 👩‍💻 Author

**Shreya Ghosh**

B.Tech – Computer Science & Business Systems (CSBS)  
Institute of Engineering & Management (IEM), Kolkata

GitHub: https://github.com/Shreya-Ghosh526

---

## 📜 License

This project is licensed under the MIT License.
