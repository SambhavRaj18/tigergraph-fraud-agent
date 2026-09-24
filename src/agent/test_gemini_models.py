import os
import requests
from dotenv import load_dotenv

load_dotenv("d:/HHHGOA/tigergraph-fraud-agent/.env", override=True)
api_key = os.environ.get("GEMINI_API_KEY")

models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"]
for m in models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "Respond strictly with JSON: {\"status\": \"ok\"}"}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"Model {m}: Status {res.status_code}")
        if res.status_code == 200:
            print("  Response:", res.json()["candidates"][0]["content"]["parts"][0]["text"])
        else:
            print("  Error:", res.text[:200])
    except Exception as e:
        print(f"Model {m} exception: {e}")
