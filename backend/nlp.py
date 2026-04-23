import os
import json
from dotenv import load_dotenv
from google import genai

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# -------------------------------
# Gemini client
# -------------------------------
client = genai.Client(api_key=API_KEY)


# -------------------------------
# PARSE QUERY (NL → STRUCTURED JSON)
# -------------------------------
def parse_query(user_query):

    prompt = f"""
You are an expert Data Analysis AI.

Convert the user query into STRICT JSON only.

---

DATASET STRUCTURE:
- name (string)
- grade (integer)
- marks (integer 0-100)

---

RULES:
1. Output ONLY JSON.
2. No explanation.
3. No markdown.
4. No extra text.

---

FIELDS:
- data_type: "student_performance"
- filters: {{"grade": number or null}}
- aggregation: "top" | "average" | "count" | null
- limit: number or null

---

LOGIC:
- "top students" → aggregation = "top"
- "average marks" → aggregation = "average"
- "how many students" → aggregation = "count"
- "top 5" → limit = 5

---

USER QUERY:
{user_query}

Return ONLY JSON:
"""

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash-latest",
            contents=prompt
        )

        text = response.text.strip()

        # remove markdown if any
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)

    except Exception as e:
        print("Parse error:", e)

        return {
            "data_type": "student_performance",
            "filters": {},
            "aggregation": None,
            "limit": None
        }


# -------------------------------
# GENERATE INSIGHTS
# -------------------------------
def generate_insight(data_text):

    prompt = f"""
You are a professional data analyst.

Give 2–3 short insights based on the data below.

RULES:
- Bullet points only
- No extra explanation
- Simple English

DATA:
{data_text}
"""

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash-latest",
            contents=prompt
        )

        return response.text.strip()

    except Exception as e:
        print("Insight error:", e)
        return "Insight generation failed."