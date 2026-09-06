from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 31)


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


def test_pure_python_dicts_fails():
    # 输出正确，但用纯 Python 字典列表手算——没有 DataFrame / iloc / loc
    code = (
        'rows = [\n'
        '    {"轮次": 1, "角色": "user", "token数": 12},\n'
        '    {"轮次": 2, "角色": "assistant", "token数": 156},\n'
        '    {"轮次": 3, "角色": "user", "token数": 8},\n'
        '    {"轮次": 4, "角色": "assistant", "token数": 203},\n'
        ']\n'
        'print(f"第一条消息来自：{rows[0][\'角色\']}")\n'
        'tokens = [r["token数"] for r in rows if r["角色"] == "assistant"]\n'
        'print(f"assistant 平均 token：{sum(tokens) / len(tokens):.1f}")\n'
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "DataFrame" in msg
