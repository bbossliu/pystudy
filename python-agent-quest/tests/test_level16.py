from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 16)


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


def test_hardcoded_prompt_in_build_prompt_fails():
    code = (
        'def build_prompt(base, injections):\n'
        '    return "你是小K，一个代码助手。\\n\\n可用工具：search、read_file\\n\\n当前用户：小明"\n'
        '\n'
        'print(build_prompt("x", []))\n'
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "join" in msg
