from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd

from nlp import parse_query, generate_insight

app = FastAPI()

# -------------------------------
# CORS (Frontend connection)
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Sample dataset
# -------------------------------
data = [
    {"name": "A", "grade": 10, "marks": 95},
    {"name": "B", "grade": 10, "marks": 90},
    {"name": "C", "grade": 9, "marks": 85},
    {"name": "D", "grade": 10, "marks": 88},
    {"name": "E", "grade": 10, "marks": 92},
]

df = pd.DataFrame(data)

# store last result for CSV download
last_result = None


# -------------------------------
# Format response
# -------------------------------
def format_response(result_df):
    if result_df is None or result_df.empty:
        return "No data found."

    text = "📊 Results:\n\n"
    for _, row in result_df.iterrows():
        text += f"• {row['name']} — {row['marks']} marks\n"
    return text


# -------------------------------
# CHAT API
# -------------------------------
@app.post("/chat")
def chat(request: dict):
    global last_result

    user_query = request.get("message", "")

    # Step 1: LLM parsing
    query_json = parse_query(user_query) or {}

    result = df.copy()

    # Step 2: Filters (safe handling)
    filters = query_json.get("filters", {})
    grade = filters.get("grade")

    if grade is not None:
        result = result[result["grade"] == grade]

    # Step 3: Aggregation logic
    aggregation = query_json.get("aggregation")

    if aggregation == "top":
        result = result.sort_values(by="marks", ascending=False)

    elif aggregation == "average":
        avg = float(result["marks"].mean()) if not result.empty else 0

        last_result = result

        return {
            "reply": f"📊 Average Marks: {round(avg, 2)}",
            "insight": "This shows overall class performance trend.",
            "download": "/download/csv"
        }

    elif aggregation == "count":
        count = len(result)

        last_result = result

        return {
            "reply": f"📊 Total Students: {count}",
            "insight": "This shows dataset size after filters.",
            "download": "/download/csv"
        }

    # Step 4: Limit handling
    limit = query_json.get("limit")

    if limit:
        result = result.head(int(limit))

    last_result = result

    # Step 5: Format output
    reply_text = format_response(result)

    # Step 6: AI insight
    insight = generate_insight(reply_text)

    return {
        "reply": reply_text,
        "insight": insight,
        "download": "/download/csv"
    }


# -------------------------------
# CSV DOWNLOAD
# -------------------------------
@app.get("/download/csv")
def download_csv():
    global last_result

    if last_result is None or last_result.empty:
        return {"error": "No report generated yet"}

    file_path = "report.csv"
    last_result.to_csv(file_path, index=False)

    return FileResponse(file_path, filename="report.csv")