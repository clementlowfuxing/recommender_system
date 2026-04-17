"""Send a test recommendation request to the running API server."""

import json
import urllib.request
import urllib.error

URL = "http://localhost:8000/recommend"

payload = {
    "required_skills": ["python", "machine_learning", "sql"],
    "required_competency_level": 4.0,
    "min_experience": 5,
    "role_level": "senior",
    "availability_required": True,
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        print(json.dumps(result, indent=2))
except urllib.error.URLError as e:
    print(f"Error connecting to server: {e}")
    print("Make sure the server is running: python app/main.py")
