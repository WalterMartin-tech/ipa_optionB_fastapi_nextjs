from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _token():
    r = client.post("/auth/login/json", json={"username":"admin@example.com","password":"admin"})
    assert r.status_code == 200
    return r.json()["access_token"]

def test_calculate_shape():
    t = _token()
    payload = {"demo": True, "principal": 100000, "rate": 0.12, "term_months": 24}
    r = client.post("/calculate", headers={"Authorization": f"Bearer {t}"}, json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "totals" in data and isinstance(data["totals"], dict)
    assert {'annuity','ipa_vat','asset_vat','vat_delta'}.issubset(set(data['totals'].keys()))
