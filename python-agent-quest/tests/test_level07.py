from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 7)


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


def test_correct_output_without_try_fails():
    code = (
        'raw_results = ["42", "abc", "7"]\n'
        "for raw in raw_results:\n"
        "    if raw.isdigit():\n"
        '        print(f"结果：{int(raw)}")\n'
        "    else:\n"
        '        print(f"跳过无效结果：{raw}")\n'
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "try" in msg
