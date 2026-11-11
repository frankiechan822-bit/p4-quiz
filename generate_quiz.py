import os
import re
import json
import urllib.request

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in environment!")

API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

PROMPT = """
You are an expert primary school examination setter for Hong Kong Primary 4 (小四).
Generate a complete JSON object containing 20 Multiple Choice questions for EACH of the following 5 subjects:
1. English: Primary 4 level grammar, tenses, connectives, prepositions, proofreading.
2. Maths: Primary 4 level, MUST include H.C.F., L.C.M., fractions addition/subtraction, perimeter/area, 3-digit multiplication/division.
3. Chinese: Primary 4 level, 錯別字, 成語, 關聯詞, 修辭, 病句, 標點.
4. Humanities: Primary 4 level Hong Kong community, Chinese festivals, civic responsibility, history & geography.
5. Science: MUST BE IN ENGLISH ONLY. Topics: Structure of the Earth (crust, mantle, core), Earth rotation and revolution (day/night, seasons, axis tilt), Types of rocks (igneous, sedimentary, metamorphic), weathering & erosion.

Output STRICTLY valid JSON with no markdown wrapping, matching this exact structure:
{
  "English": [
    {"id": 1, "category": "Simple Past", "question": "...", "options": ["A", "B", "C", "D"], "answer": 0, "explanation": "..."}
  ],
  "Maths": [... 20 items ...],
  "Chinese": [... 20 items ...],
  "Humanities": [... 20 items ...],
  "Science": [... 20 items ...]
}
Note: "answer" must be the 0-based index of the correct option (0 for A, 1 for B, 2 for C, 3 for D).
"""

payload = {
    "contents": [{"parts": [{"text": PROMPT}]}],
    "generationConfig": {"response_mime_type": "application/json"}
}

req = urllib.request.Request(
    API_URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

print("Calling Gemini API to generate daily quiz...")
with urllib.request.urlopen(req) as response:
    result = json.loads(response.read().decode("utf-8"))

generated_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
quiz_data = json.loads(generated_text)

# 讀取 index.html 並將 p4Database 變數無縫替換
with open("index.html", "r", encoding="utf-8") as f:
    html_content = f.read()

pattern = r"const p4Database = \{[\s\S]*?\n    \};"
replacement = f"const p4Database = {json.dumps(quiz_data, ensure_ascii=False, indent=2)};"

new_html = re.sub(pattern, replacement, html_content)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(new_html)

print("index.html successfully updated with fresh P4 questions!")
