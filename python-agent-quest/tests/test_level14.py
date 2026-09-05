import os

import pytest

from server.levels.loader import load_levels
from server.runner import RunResult, run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 14)


def _ok_result(stdout="小K：你好，我是 DeepSeek。\n"):
    return RunResult(stdout, "", 0, False, "/tmp/fake")


def test_level_has_custom_timeout():
    assert _level().timeout == 60


def test_default_timeout_for_other_levels():
    lv = next(lv for lv in load_levels() if lv.id == 13)
    assert lv.timeout == 5


def test_judge_rejects_missing_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    lv = _level()
    passed, msg = lv.judge(lv.solution, _ok_result())
    assert not passed
    assert "DEEPSEEK_API_KEY" in msg


def test_judge_rejects_hardcoded_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "whatever")
    code = _level().solution.replace(
        'os.environ.get("DEEPSEEK_API_KEY")', '"sk-fakehardcodedkey123"'
    )
    passed, msg = _level().judge(code, _ok_result())
    assert not passed
    assert "硬编码" in msg


def test_judge_reports_runtime_error(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "whatever")
    r = RunResult("", "Traceback ...\nNameError: name '___' is not defined", 1, False, "/tmp/fake")
    passed, msg = _level().judge(_level().solution, r)
    assert not passed
    assert "报错" in msg


def test_judge_special_cases_auth_error(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "whatever")
    r = RunResult("", "openai.AuthenticationError: Error code: 401", 1, False, "/tmp/fake")
    passed, msg = _level().judge(_level().solution, r)
    assert not passed
    assert "401" in msg
    assert "key" in msg


def test_judge_rejects_missing_prefix(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "whatever")
    passed, msg = _level().judge(_level().solution, _ok_result(stdout="你好\n"))
    assert not passed
    assert "小K：" in msg


def test_judge_rejects_no_openai_client(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "whatever")
    code = (
        "import os\n"
        'key = os.environ.get("DEEPSEEK_API_KEY")\n'
        'print("小K：我是假回复")\n'
    )
    passed, msg = _level().judge(code, _ok_result())
    assert not passed
    assert "OpenAI" in msg


def test_judge_rejects_no_env_read(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "whatever")
    code = (
        "from openai import OpenAI\n"
        'client = OpenAI(base_url="https://api.deepseek.com", api_key=get_key())\n'
        'print("小K：hi")\n'
    )
    passed, msg = _level().judge(code, _ok_result())
    assert not passed
    assert "环境变量" in msg


def test_starter_fails_judge(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "whatever")
    lv = _level()
    r = run_code(lv.starter_code, timeout=lv.timeout)
    passed, msg = lv.judge(lv.starter_code, r)
    assert not passed
    assert msg


@pytest.mark.skipif(not os.environ.get("DEEPSEEK_API_KEY"), reason="需要 DEEPSEEK_API_KEY")
def test_solution_passes_with_real_api():
    lv = _level()
    r = run_code(lv.solution, timeout=lv.timeout)
    passed, msg = lv.judge(lv.solution, r)
    assert passed, msg
