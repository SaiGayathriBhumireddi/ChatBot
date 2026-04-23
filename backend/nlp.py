import os
import json
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# -------------------------------
# CLEAN TEXT FROM GEMINI
# -------------------------------
def clean_json(text: str):
    text = re.sub(r"```json|```", "", text).strip()
    return text


# -------------------------------
# FALLBACK REGEX PARSER (IMPORTANT)
# -------------------------------
def fallback_parse(user_query: str):
    query = user_query.lower()

    result = {
        "data_type": "student_performance",
        "filters": {"grade": None},
        "aggregation": None,
        "limit": None
    }

    # grade extraction
    grade_match = re.search(r"grade\s*(\d+)", query)
    if grade_match:
        result["filters"]["grade"] = int(grade_match.group(1))

    # limit extraction
    limit_match = re.search(r"(top|show)\s*(\d+)", query)
    if limit_match:
        result["limit"] = int(limit_match.group(2))

    # aggregation
    if "average" in query or "mean" in query:
        result["aggregation"] = "average"
    elif "top" in query:
        result["aggregation"] = "top"
    elif "count" in query:
        result["aggregation"] = "count"

    return result


# -------------------------------
# MAIN PARSER (LLM + SAFE FALLBACK)
# -------------------------------
def parse_query(user_query: str):

    prompt = f"""
You are a STRICT JSON extraction engine for student analytics.

Return ONLY valid JSON.

Dataset:
name, grade, marks

Rules:
- Extract grade if mentioned
- Detect aggregation: top, average, count, null
- Extract limit if mentioned

Output format:
{{
  "data_type": "student_performance",
  "filters": {{
    "grade": null
  }},
  "aggregation": null,
  "limit": null
}}

User query:
{user_query}

Return ONLY JSON.
"""

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )

        text = clean_json(response.text)
        parsed = json.loads(text)

        # 🔥 validation fix
        if not isinstance(parsed, dict):
            return fallback_parse(user_query)

        return parsed

    except Exception as e:
        print("LLM failed → using fallback:", e)
        return fallback_parse(user_query)


# -------------------------------
# INSIGHT GENERATION
# -------------------------------
def generate_insight(text: str):
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"Summarize this in 1-2 lines:\n{text}"
        )
        return response.text.strip()
    except:
        return "Insight not available."