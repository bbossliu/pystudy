from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 6)


def test_solution_passes():
    lv = _level()
    r = run_code(lv.solution)
    passed, msg = lv.judge(lv.solution, r)
    assert passed, msg


def test_starter_fails():
    lv = _level()
    r = run_code(lv.starter_code)
    passed, msg = lv.judge(lv.starter_code, r)
    assert not passed
    assert msg


def test_correct_output_without_function_fails():
    code = (
        'print("[mock-pro] 回复：你好 的模拟回答")\n'
        'print("[mock-1] 回复：介绍一下你自己 的模拟回答")\n'
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "call_llm" in msg
