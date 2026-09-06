from server.levels.loader import load_levels
from server.runner import run_code


def test_loads_level01():
    levels = load_levels()
    assert len(levels) >= 1
    lv = levels[0]
    assert lv.id == 1
    assert "小K" in lv.story


def test_level01_judge_accepts_solution():
    lv = load_levels()[0]
    r = run_code(lv.solution)
    passed, _ = lv.judge(lv.solution, r)
    assert passed


def test_level01_judge_rejects_wrong_output():
    lv = load_levels()[0]
    code = 'name = "小K"\nrole = "代码助手"\nprint(f"我是{name}")'
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "输出不对" in msg


def test_level01_judge_rejects_non_fstring():
    lv = load_levels()[0]
    code = 'name = "小K"\nrole = "代码助手"\nprint("你是" + name + "，一个" + role + "。")'
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "f-string" in msg


def test_level01_judge_rejects_crashing_code():
    lv = load_levels()[0]
    code = "raise RuntimeError('boom')"
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "报错" in msg
