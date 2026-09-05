from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 8)


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


def test_correct_output_without_file_fails():
    code = 'print("已保存 1 条记忆")\n'
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "memory.json" in msg
