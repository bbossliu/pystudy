from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 5)


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


def test_correct_output_without_for_and_listcomp_fails():
    code = (
        'print("步骤 1：理解问题")\n'
        'print("步骤 2：搜索资料")\n'
        'print("步骤 3：生成回答")\n'
        "print(['理解问题-完成', '搜索资料-完成', '生成回答-完成'])\n"
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "for" in msg
