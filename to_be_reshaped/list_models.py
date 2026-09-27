# list_models.py: print the model names your Ask Sage account can use.
import os
import requests
from dotenv import load_dotenv

load_dotenv()
login = requests.post(
    "https://api.asksage.ai.nasa.gov/user/get-token-with-api-key",
    json={"email": os.getenv("ASKSAGE_EMAIL"),
          "api_key": os.getenv("ASKSAGE_API_KEY")},
    timeout=(5, 60))
login.raise_for_status()
payload = login.json()["response"]
token = payload["access_token"] if isinstance(payload, dict) else payload

resp = requests.post("https://api.asksage.ai.nasa.gov/server/get-models",
                     headers={"x-access-tokens": token}, timeout=(5, 60))
resp.raise_for_status()
print(resp.json())
