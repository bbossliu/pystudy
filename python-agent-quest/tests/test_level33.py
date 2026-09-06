from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 33)


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


def test_pure_python_cleaning_fails():
    # 输出正确，但用纯 Python 手写清洗——没有 .str 访问器和 fillna/dropna
    code = (
        'roles = ["User", "assistant", "USER", "Assistant", "tool", "ASSISTANT"]\n'
        'tokens = [12, None, 8, None, 156, 202]\n'
        'roles = [r.lower() for r in roles]\n'
        'vals = [t for t in tokens if t is not None]\n'
        'mean = sum(vals) / len(vals)\n'
        'tokens = [t if t is not None else mean for t in tokens]\n'
        'print(f"user 条数：{sum(1 for r in roles if r == \'user\')}")\n'
        'print(f"清洗后总 token：{int(sum(tokens))}")\n'
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert ".str" in msg
