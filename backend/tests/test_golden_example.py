import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _token():
    r = client.post("/auth/login/json", json={"username":"admin@example.com","password":"admin"})
    assert r.status_code == 200
    return r.json()["access_token"]

def test_golden_example():
    t = _token()
    case = json.load(open("tests/cases/example_case.json"))
    r = client.post("/calculate", headers={"Authorization": f"Bearer {t}"}, json=case["input"])
    assert r.status_code == 200
    totals = r.json()["totals"]
    assert totals == case["expected_totals"]
