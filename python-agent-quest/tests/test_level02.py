from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 2)


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


def test_correct_output_without_append_fails():
    code = (
        'messages = ["[system] 你是小K，一个代码助手。", '
        '"[user] 你能帮我写代码吗？", "[assistant] 当然可以！"]\n'
        "for msg in messages:\n"
        "    print(msg)\n"
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "append" in msg
