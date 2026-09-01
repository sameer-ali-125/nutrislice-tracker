import requests
import os
import resend
from dotenv import load_dotenv
load_dotenv()
from datetime import date

today = date.today()
year = today.year
month = today.month
day = today.day

url = f"https://stonybrook.api.nutrislice.com/menu/api/weeks/school/west-side-dining/menu-type/todays-dine-in-specials-wsd/{year}/{month:02d}/{day:02d}/"

response = requests.get(url)
data = response.json()

today_str = today.isoformat()

todays_menu = None
for day_entry in data["days"]:
    if day_entry["date"] == today_str:
        todays_menu = day_entry
        break

def detect_meal(station_text):
    text_lower = station_text.lower()
    if "breakfast" in text_lower:
        return "Breakfast"
    elif "lunch" in text_lower:
        return "Lunch"
    elif "dinner" in text_lower:
        return "Dinner"
    elif "late night" in text_lower:
        return "Late Night"
    else:
        return None

search_terms = ["orzo", "orange chicken"]
matches = []
current_station = None
current_meal = "Lunch"  # default assumption when a station's meal isn't explicit

for item in todays_menu["menu_items"]:
    if item["is_section_title"]:
        current_station = item["text"]
        detected_meal = detect_meal(current_station)

        if detected_meal == "Breakfast":
            current_meal = "Breakfast"
        elif detected_meal in ("Dinner", "Late Night"):
            current_meal = detected_meal
        elif detected_meal == "Lunch":
            current_meal = "Lunch"
        elif detected_meal is None and current_meal == "Breakfast":
            # an ambiguous station right after Breakfast is assumed
            # to have moved on to Lunch, since Breakfast doesn't "stick"
            current_meal = "Lunch"
        continue

    food_name = item["food"]["name"]
    food_name_lower = food_name.lower()

    for term in search_terms:
        if term in food_name_lower:
            matches.append({
                "term": term,
                "food_name": food_name,
                "station": current_station,
                "meal": current_meal
            })

print("Matches found today:")
for match in matches:
    print(f"- {match['food_name']} at {match['station']} ({match['meal']})")

def send_email(matches):
    resend.api_key = os.getenv("RESEND_API_KEY")
    destination = os.getenv("GMAIL_ADDRESS")

    if not matches:
        body = "No matches found today."
    else:
        lines = []
        for match in matches:
            lines.append(f"- {match['food_name']} at {match['station']} ({match['meal']})")
        body = "\n".join(lines)

    resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": destination,
        "subject": "Nutrislice Daily Check: West Side Dining",
        "text": body
    })

    print("Email sent!")

send_email(matches)
    
