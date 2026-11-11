import os
import re
import json
import time
import urllib.request
import urllib.error

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("FATAL: GEMINI_API_KEY is not set in Secrets!")
    exit(1)

# 使用 Google 官方當前開放的標準 REST 端點
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"

# 5 個科目的專屬出題要求（小四程度）
SUBJECT_PROMPTS = {
    "english.html": (
        "Primary 4 English for Hong Kong schools",
        "Generate 20 Multiple Choice questions covering: Simple Past Tense, Connectives (so, but, because, although), Prepositions, Comparatives/Superlatives, Quantifiers, and Proofreading. Questions and options must be in English."
    ),
    "maths.html": (
        "香港小學四年級數學科",
        "生成 20 條四選一選擇題。必須重點包含：求兩數及三數的最大公因數 (H.C.F.) 與最小公倍數 (L.C.M.)、HCF/LCM 情境應用題（如彩帶等長剪切、鐘聲班次同時鳴響）、同分母分數加減、三位數乘除、周界與長方形/正方形面積。"
    ),
    "chinese.html": (
        "香港小學四年級中文科",
        "生成 20 條四選一選擇題。考核範疇：錯別字辨識、成語運用與正字、關聯詞搭配（只有才、雖然但是、即使也）、修辭手法辨析（比喻、擬人、排比）、病句辨析、標點符號與規範書面語。"
    ),
    "humanities.html": (
        "香港小學四年級人文科",
        "生成 20 條四選一選擇題。考核範疇：香港三大區域與地理特徵、中華傳統文化節慶、公民公德心與長幼相處、香港歷史古蹟地標、環境保護與三色分類回收、緊急求助與公共秩序。"
    ),
    "science.html": (
        "Primary 4 Science (MUST BE FULLY IN ENGLISH)",
        "Generate 20 Multiple Choice questions. Topics: 1. Structure of the Earth (Crust, Mantle, Outer Core, Inner Core), 2. Earth's Rotation and Revolution (Day & night, seasons, axis tilt, 24h vs 365.25 days), 3. Types of Rocks (Igneous, Sedimentary, Metamorphic, Granite in HK, Fossils, Weathering and Erosion). Questions and explanations MUST be in English only."
    )
}

def generate_questions_for_subject(sub_name, sub_req):
    prompt_text = f"""
You are an expert exam setter for Hong Kong Primary 4.
Task: {sub_req}

Output STRICTLY a valid JSON array containing exactly 20 question objects, with NO markdown formatting, NO backticks:
[
  {{
    "id": 1,
    "category": "Topic Name",
    "question": "Question text...",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": 0,
    "explanation": "Concise step-by-step reason or calculation."
  }}
]
Note: "answer" must be the 0-based integer index of the correct option (0 for A, 1 for B, 2 for C, 3 for D).
"""
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.8
        }
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    for attempt in range(3):
        try:
            print(f"Calling Gemini API for {sub_name} (Attempt {attempt+1})...")
            with urllib.request.urlopen(req, timeout=60) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                q_list = json.loads(text)
                if isinstance(q_list, list) and len(q_list) >= 15:
                    for idx, q in enumerate(q_list):
                        q["id"] = idx + 1
                    return q_list
        except Exception as e:
            print(f"Attempt {attempt+1} failed for {sub_name}: {e}")
            time.sleep(3)

    return None

# 逐一生成各科試題並注入對應網頁
for file_name, (sub_display, sub_req) in SUBJECT_PROMPTS.items():
    if not os.path.exists(file_name):
        continue

    print(f"\n--- Generating NEW questions for {file_name} ({sub_display}) ---")
    new_questions = generate_questions_for_subject(file_name, sub_req)

    if not new_questions:
        print(f"Skipping {file_name} due to API failure. Keeping existing questions.")
        continue

    with open(file_name, "r", encoding="utf-8") as f:
        html_content = f.read()

    # 替換網頁內部的 questions 陣列
    pattern = r'const questions = (\[[\s\S]*?\]);'
    new_q_str = f"const questions = {json.dumps(new_questions, ensure_ascii=False, indent=2)};"
    updated_html = re.sub(pattern, new_q_str, html_content)

    with open(file_name, "w", encoding="utf-8") as f:
        f.write(updated_html)

    print(f"SUCCESS: {file_name} has been updated with 20 brand-new AI generated questions!")
    time.sleep(2)
