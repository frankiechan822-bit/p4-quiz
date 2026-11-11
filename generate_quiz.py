import os
import re
import json
import google.generativeai as genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY is missing in GitHub Secrets!")
    exit(1)

genai.configure(api_key=api_key)

# 自動列出目前此 Key 真正支援 generateContent 的可用模型
available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
print(f"Available models for this key: {available_models}")

# 優先選擇 flash，若無則挑選第一個可用模型
selected_model_name = None
for m in available_models:
    if "flash" in m:
        selected_model_name = m
        break
if not selected_model_name and available_models:
    selected_model_name = available_models[0]

if not selected_model_name:
    print("ERROR: No available generateContent models found.")
    exit(1)

print(f"Using model: {selected_model_name}")
model = genai.GenerativeModel(selected_model_name)

PROMPT = """
You are an expert examination setter for Hong Kong Primary 4 (小四).
Generate a valid JSON object containing 20 Multiple Choice questions for EACH of the following 5 subjects:
1. English: Primary 4 level grammar, tenses, connectives, prepositions, proofreading.
2. Maths: Primary 4 level, MUST include H.C.F., L.C.M., fractions addition/subtraction, perimeter/area, 3-digit multiplication/division.
3. Chinese: Primary 4 level, 錯別字, 成語, 關聯詞, 修辭, 病句, 標點.
4. Humanities: Primary 4 level Hong Kong community, Chinese festivals, civic responsibility, history & geography.
5. Science: MUST BE IN ENGLISH ONLY. Topics: Structure of the Earth (crust, mantle, core), Earth rotation and revolution (day/night, seasons, axis tilt), Types of rocks (igneous, sedimentary, metamorphic), weathering & erosion.

Output STRICTLY valid JSON with no markdown wrapping:
{
  "English": [{"id": 1, "category": "Grammar", "question": "...", "options": ["A", "B", "C", "D"], "answer": 0, "explanation": "..."}],
  "Maths": [... 20 items ...],
  "Chinese": [... 20 items ...],
  "Humanities": [... 20 items ...],
  "Science": [... 20 items ...]
}
"answer" must be the 0-based integer index (0 for A, 1 for B, 2 for C, 3 for D). Keep explanation concise.
"""

response = model.generate_content(
    PROMPT,
    generation_config=genai.types.GenerationConfig(
        response_mime_type="application/json",
        max_output_tokens=8192,
        temperature=0.7
    )
)

generated_text = response.text.strip()
quiz_data = json.loads(generated_text)

# 讀取 index.html 並將 p4Database 變數無縫替換
with open("index.html", "r", encoding="utf-8") as f:
    html_content = f.read()

pattern = r"const p4Database = \{[\s\S]*?\n    \};"
replacement = f"const p4Database = {json.dumps(quiz_data, ensure_ascii=False, indent=2)};"

new_html = re.sub(pattern, replacement, html_content)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(new_html)

print("Success: index.html has been updated with 100 fresh P4 questions!")
