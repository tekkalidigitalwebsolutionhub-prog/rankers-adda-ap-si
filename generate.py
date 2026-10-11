import json
import os
from pathlib import Path

TOTAL_DAYS = 60
QUESTIONS_PER_DAY = 200


def load_api_key():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        return api_key

    env_file = Path(__file__).resolve().parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = [part.strip() for part in line.split("=", 1)]
            if key in {"GEMINI_API_KEY", "GOOGLE_API_KEY"}:
                return value.strip('"\'')

    raise RuntimeError(
        "GEMINI_API_KEY is missing. Set it as an environment variable or add a .env file with GEMINI_API_KEY=YOUR_KEY"
    )


API_KEY = load_api_key()

try:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=API_KEY)
    model_name = "gemini-2.0-flash"

    def generate_content(prompt):
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return response.text

except Exception:
    import google.generativeai as genai

    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        generation_config={"response_mime_type": "application/json"},
    )

    def generate_content(prompt):
        return model.generate_content(prompt).text


os.makedirs("data", exist_ok=True)

print("Rankers Adda - AP Police SI AI Question Generator ప్రారంభమైంది...")
print(f"మొత్తం రోజులు: {TOTAL_DAYS} | ప్రతి రోజుకు: {QUESTIONS_PER_DAY} ప్రశ్నలు")

for day in range(1, TOTAL_DAYS + 1):
    print(f"దినం {day} ({QUESTIONS_PER_DAY} ప్రశ్నలు) జనరేట్ చేయబడుతున్నాయి...")

    prompt = f"""
    నీవు ఒక నిపుణుడైన AP Police SI ఎగ్జామ్ కోచింగ్ ఫ్యాకల్టీవి.
    AP Police SI Prelims పరీక్షా ప్రమాణాల (50 అంకగణితం, 50 రీజనింగ్, 100 జనరల్ స్టడీస్) ఆధారంగా దినం {day} కొరకు పూర్తిగా విభిన్నమైన మరియు నాణ్యమైన {QUESTIONS_PER_DAY} ఒరిజినల్ ప్రశ్నలను అచ్చమైన తెలుగు లిపిలో (Telugu Script) తయారు చేయి.

    ప్రతి ప్రశ్నకు ఆప్షన్లు మరియు వివరణ (explanation) తప్పనిసరిగా ఉండాలి.
    దయచేసి కేవలం వాలిడ్ JSON ఫార్మాట్ లో మాత్రమే రెస్పాన్స్ ఇవ్వు (అదనపు టెక్స్ట్ లేదా మార్క్‌డౌన్ లేకుండా):
    [
        {{
            "section": "PAPER-1: అంకగణితం (Arithmetic)",
            "q": "ప్రశ్న పాఠ్యం...",
            "opts": ["ఆప్షన్ 1", "ఆప్షన్ 2", "ఆప్షన్ 3", "ఆప్షన్ 4"],
            "correct": 0,
            "exp": "వివరణ..."
        }}
    ]
    """

    try:
        text_res = generate_content(prompt).strip()

        if text_res.startswith("```json"):
            text_res = text_res[7:]
        if text_res.startswith("```"):
            text_res = text_res[3:]
        if text_res.endswith("```"):
            text_res = text_res[:-3]

        questions = json.loads(text_res.strip())
        if not isinstance(questions, list):
            raise ValueError("Gemini response is not a JSON array.")

        if len(questions) != QUESTIONS_PER_DAY:
            print(
                f"హెచ్చుతగ్గు: దినం {day} కోసం {len(questions)} ప్రశ్నలు వచ్చాయి; అవసరం {QUESTIONS_PER_DAY}."
            )

        file_path = os.path.join("data", f"day{day}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False, indent=4)

        print(f"దినం {day} విజయవంతంగా సేవ్ చేయబడింది! ({len(questions)} ప్రశ్నలు)")
    except Exception as e:
        print(f"దినం {day} జనరేట్ చేయడంలో లోపం ఏర్పడింది: {e}")

print("అన్ని టెస్ట్ ఫైల్స్ విజయవంతంగా జనరేట్ అయ్యాయి!")
