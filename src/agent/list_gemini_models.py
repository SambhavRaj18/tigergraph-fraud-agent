import os
import requests
from dotenv import load_dotenv

load_dotenv("d:/HHHGOA/tigergraph-fraud-agent/.env", override=True)
api_key = os.environ.get("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
res = requests.get(url)
print("ListModels Status:", res.status_code)
if res.status_code == 200:
    models = res.json().get("models", [])
    print("Available Models:")
    for m in models:
        methods = m.get("supportedGenerationMethods", [])
        if "generateContent" in methods:
            print(" -", m.get("name"))
else:
    print("Error:", res.text)
