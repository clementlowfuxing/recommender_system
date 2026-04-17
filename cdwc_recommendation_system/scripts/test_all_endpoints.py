"""Test all REST API endpoints using FastAPI TestClient (no server needed)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 1. POST /recommend
print("=== POST /recommend ===")
r = client.post("/recommend", json={
    "required_skills": ["python", "sql"],
    "required_competency_level": 3.5,
    "min_experience": 3,
    "role_level": "mid",
    "availability_required": True,
})
data = r.json()
print(f"Status: {r.status_code}")
print(f"request_id: {data.get('request_id')}")
print(f"Candidates evaluated: {data['total_candidates_evaluated']}")
print(f"After filtering: {data['candidates_after_filtering']}")
top = data["recommendations"][0]
print(f"Top candidate: {top['name']} (score {top['total_score']})")
req_id = data["request_id"]

# 2. GET /history
print("\n=== GET /history ===")
r = client.get("/history")
hist = r.json()
print(f"Status: {r.status_code}")
print(f"Total entries: {hist['total']}")
print(f"Latest entry ID: {hist['entries'][0]['request_id']}")

# 3. GET /history/{id}
print(f"\n=== GET /history/{req_id} ===")
r = client.get(f"/history/{req_id}")
print(f"Status: {r.status_code}")
entry = r.json()
print(f"Timestamp: {entry['timestamp']}")
print(f"Request skills: {entry['request']['required_skills']}")

# 4. GET /config/weights
print("\n=== GET /config/weights ===")
r = client.get("/config/weights")
print(f"Status: {r.status_code}")
print(f"Weights: {r.json()['weights']}")

# 5. PUT /config/weights (valid)
print("\n=== PUT /config/weights (valid) ===")
r = client.put("/config/weights", json={
    "skill_overlap": 0.40,
    "competency": 0.20,
    "experience": 0.25,
    "role_match": 0.15,
})
print(f"Status: {r.status_code}")
print(f"Response: {r.json()}")

# 6. PUT /config/weights (bad sum — should fail)
print("\n=== PUT /config/weights (bad sum) ===")
r = client.put("/config/weights", json={
    "skill_overlap": 0.50,
    "competency": 0.50,
    "experience": 0.50,
    "role_match": 0.50,
})
print(f"Status: {r.status_code}")
print(f"Detail: {r.json()['detail']}")

# 7. GET /history/NONEXISTENT (should 404)
print("\n=== GET /history/NONEXISTENT ===")
r = client.get("/history/REQ-9999")
print(f"Status: {r.status_code}")
print(f"Detail: {r.json()['detail']}")

print("\n=== All endpoint tests complete ===")
