from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_list_levels_hides_solution():
    resp = client.get("/api/levels")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["id"] == 1
    assert "starter_code" in data[0]
    assert "solution" not in data[0]


def test_run_endpoint_passes_with_solution():
    from server.levels.loader import load_levels

    solution = load_levels()[0].solution
    resp = client.post("/api/run", json={"level_id": 1, "code": solution})
    assert resp.status_code == 200
    assert resp.json()["passed"] is True


def test_run_endpoint_fails_with_starter_code():
    resp = client.post("/api/run", json={"level_id": 1, "code": "print('hi')"})
    assert resp.status_code == 200
    assert resp.json()["passed"] is False
    assert resp.json()["message"] != ""


def test_run_endpoint_404_for_unknown_level():
    resp = client.post("/api/run", json={"level_id": 999, "code": "pass"})
    assert resp.status_code == 404
