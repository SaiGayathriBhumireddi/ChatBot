from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd

from nlp import parse_query, generate_insight

app = FastAPI()

# -------------------------------
# CORS
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# DATASET
# -------------------------------
data = [
    {"name": "A", "grade": 10, "marks": 95},
    {"name": "B", "grade": 10, "marks": 90},
    {"name": "C", "grade": 9, "marks": 85},
    {"name": "D", "grade": 10, "marks": 88},
    {"name": "E", "grade": 10, "marks": 92},
]

df = pd.DataFrame(data)

last_result = None


# -------------------------------
# FORMAT OUTPUT
# -------------------------------
def format_response(result_df):
    if result_df.empty:
        return "No data found."

    text = "📊 Results:\n\n"
    for _, row in result_df.iterrows():
        text += f"• {row['name']} — {row['marks']} marks\n"
    return text


# -------------------------------
# CHAT ENDPOINT
# -------------------------------
@app.post("/chat")
def chat(request: dict):
    global last_result

    user_query = request.get("message", "")

    query_json = parse_query(user_query)

    print("DEBUG QUERY:", query_json)  # 🔥 IMPORTANT DEBUG

    result = df.copy()

    # -------------------------------
    # FILTER (FIXED)
    # -------------------------------
    filters = query_json.get("filters") or {}
    grade = filters.get("grade")

    if grade is not None:
        result = result[result["grade"] == grade]

    # -------------------------------
    # AGGREGATION
    # -------------------------------
    agg = query_json.get("aggregation")

    if agg == "average":
        avg = result["marks"].mean()

        reply = f"📊 Average Marks: {round(avg, 2)}"
        insight = generate_insight(reply)

        return {
            "reply": reply,
            "insight": insight,
            "download": "/download/csv"
        }

    if agg == "top":
        result = result.sort_values(by="marks", ascending=False)

    # -------------------------------
    # LIMIT
    # -------------------------------
    limit = query_json.get("limit")
    if limit:
        result = result.head(limit)

    last_result = result

    reply_text = format_response(result)
    insight = generate_insight(reply_text)

    return {
        "reply": reply_text,
        "insight": insight,
        "download": "/download/csv"
    }


# -------------------------------
# DOWNLOAD
# -------------------------------
@app.get("/download/csv")
def download_csv():
    global last_result

    if last_result is None:
        return {"error": "No report generated yet"}

    file_path = "report.csv"
    last_result.to_csv(file_path, index=False)

    return FileResponse(file_path, filename="report.csv")