import os
import requests
import json
from dotenv import load_dotenv

load_dotenv("d:/HHHGOA/tigergraph-fraud-agent/.env", override=True)
api_key = os.environ.get("GEMINI_API_KEY")

models = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.8-flash", "gemini-flash-latest", "gemini-pro-latest"]
for m in models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "Respond in JSON: {\"status\": \"ok\"}"}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"Model {m:<20s} Status: {res.status_code}")
        if res.status_code == 200:
            print("  Response:", res.json()["candidates"][0]["content"]["parts"][0]["text"])
    except Exception as e:
        print(f"Model {m} error: {e}")
