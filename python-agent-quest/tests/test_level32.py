from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 32)


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


def test_pure_python_loop_fails():
    # 输出正确，但用纯 Python 推导式 + 内置函数手算——没有布尔筛选和 Series 聚合
    code = (
        'log = [\n'
        '    {"角色": "user", "token数": 12},\n'
        '    {"角色": "assistant", "token数": 156},\n'
        '    {"角色": "user", "token数": 8},\n'
        '    {"角色": "assistant", "token数": 203},\n'
        ']\n'
        'tokens = [r["token数"] for r in log]\n'
        'slow = [t for t in tokens if t > 100]\n'
        'print(f"慢对话条数：{len(slow)}")\n'
        'print(f"最慢的一条：{max(slow)}")\n'
        'print(f"总 token：{sum(tokens)}")\n'
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "布尔筛选" in msg
