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
    for level in data:
        assert "solution" not in level


def test_list_levels_includes_diagram_field():
    resp = client.get("/api/levels")
    assert resp.status_code == 200
    for level in resp.json():
        assert "diagram" in level


def test_level15_has_diagram():
    resp = client.get("/api/levels")
    data = resp.json()
    lv15 = next(lv for lv in data if lv["id"] == 15)
    assert lv15["diagram"]


def test_run_endpoint_passes_with_solution():
    from server.levels.loader import load_levels

    solution = load_levels()[0].solution
    resp = client.post("/api/run", json={"level_id": 1, "code": solution})
    assert resp.status_code == 200
    assert resp.json()["passed"] is True


def test_run_endpoint_fails_with_starter_code():
    from server.levels.loader import load_levels

    starter = load_levels()[0].starter_code
    resp = client.post("/api/run", json={"level_id": 1, "code": starter})
    assert resp.status_code == 200
    assert resp.json()["passed"] is False
    assert resp.json()["message"] != ""


def test_run_endpoint_cleans_up_workdir(monkeypatch, tmp_path):
    import os

    import server.main as main_mod
    from server.runner import RunResult

    workdir = tmp_path / "fake_quest"
    workdir.mkdir()
    (workdir / "a.txt").write_text("hi")
    fake = RunResult("你是小K，一个代码助手。\n", "", 0, False, str(workdir))
    monkeypatch.setattr(main_mod, "run_code", lambda code, timeout=5: fake)
    resp = client.post("/api/run", json={"level_id": 1, "code": "xxx"})
    assert resp.status_code == 200
    assert not os.path.exists(workdir)


def test_run_endpoint_timeout():
    resp = client.post("/api/run", json={"level_id": 1, "code": "while True: pass"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["passed"] is False
    assert "超时" in data["message"]


def test_run_endpoint_404_for_unknown_level():
    resp = client.post("/api/run", json={"level_id": 999, "code": "pass"})
    assert resp.status_code == 404
