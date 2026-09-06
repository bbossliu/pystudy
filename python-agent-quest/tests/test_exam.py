from fastapi.testclient import TestClient

from server.exam import PASSING_SCORE, QUESTIONS
from server.main import app

client = TestClient(app)

TOTAL = len(QUESTIONS)


def _all_correct_answers():
    return {str(q["id"]): q["answer"] for q in QUESTIONS}


def _all_wrong_answers():
    # 选一个一定不等于答案的下标
    return {str(q["id"]): (q["answer"] + 1) % 4 for q in QUESTIONS}


# ---- 题库本身的质量约束 ----


def test_question_bank_shape():
    assert TOTAL == 20
    assert PASSING_SCORE == 80
    ids = [q["id"] for q in QUESTIONS]
    assert len(set(ids)) == TOTAL  # id 不重复
    for q in QUESTIONS:
        assert q["question"]
        assert len(q["options"]) == 4
        assert 0 <= q["answer"] < 4
        assert q["explanation"]
        assert 1 <= q["level_id"] <= 41


def test_question_bank_series_distribution():
    def count(lo, hi):
        return sum(1 for q in QUESTIONS if lo <= q["level_id"] <= hi)

    assert count(1, 12) == 5    # 语法
    assert count(13, 14) == 2   # 造 agent
    assert count(15, 22) == 4   # deepagents
    assert count(23, 28) == 4   # dsh
    assert count(29, 34) == 2   # 数据处理
    assert count(35, 41) == 3   # 基础补强


# ---- GET /api/exam：不泄露答案 ----


def test_get_exam_returns_20_questions():
    resp = client.get("/api/exam")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 20
    for q in data:
        assert "id" in q
        assert "question" in q
        assert len(q["options"]) == 4


def test_get_exam_never_leaks_answer_or_explanation():
    resp = client.get("/api/exam")
    assert resp.status_code == 200
    for q in resp.json():
        assert "answer" not in q
        assert "explanation" not in q
        assert "level_id" not in q
    # 整个响应体里也不许出现任何一题的解析原文
    for q in QUESTIONS:
        assert q["explanation"] not in resp.text


# ---- POST /api/exam/submit ----


def test_submit_all_correct_scores_100_and_passes():
    resp = client.post("/api/exam/submit", json={"answers": _all_correct_answers()})
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 100
    assert data["passed"] is True
    assert data["total"] == 20
    assert all(r["correct"] for r in data["results"])


def test_submit_all_wrong_scores_0_with_explanations():
    resp = client.post("/api/exam/submit", json={"answers": _all_wrong_answers()})
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 0
    assert data["passed"] is False
    for r in data["results"]:
        assert r["correct"] is False
        assert r["explanation"]
        assert isinstance(r["level_id"], int)
        assert r["your_choice"] != r["correct_choice"]


def test_submit_half_correct_scores_50_and_fails():
    answers = {}
    for i, q in enumerate(QUESTIONS):
        answers[str(q["id"])] = q["answer"] if i % 2 == 0 else (q["answer"] + 1) % 4
    resp = client.post("/api/exam/submit", json={"answers": answers})
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 50
    assert data["passed"] is False


def test_submit_unanswered_counts_as_wrong():
    resp = client.post("/api/exam/submit", json={"answers": {}})
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 0
    assert data["passed"] is False
    assert all(r["your_choice"] is None for r in data["results"])


def test_submit_unknown_question_ids_are_ignored():
    answers = _all_correct_answers()
    answers["999"] = 0
    answers["abc"] = 1
    resp = client.post("/api/exam/submit", json={"answers": answers})
    assert resp.status_code == 200
    assert resp.json()["score"] == 100
