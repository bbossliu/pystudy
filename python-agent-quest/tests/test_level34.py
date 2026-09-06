from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 34)


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


def test_pure_python_grouping_fails():
    # 输出正确（手工对齐 pandas 打印格式），但用纯 Python 字典分堆——没有 groupby
    code = (
        'rows = [\n'
        '    ("user", 15), ("assistant", 180), ("tool", 45), ("user", 10),\n'
        '    ("assistant", 220), ("tool", 60), ("assistant", 170),\n'
        ']\n'
        'sums, counts = {}, {}\n'
        'for role, t in rows:\n'
        '    sums[role] = sums.get(role, 0) + t\n'
        '    counts[role] = counts.get(role, 0) + 1\n'
        'print("角色")\n'
        'for role in sorted(sums):\n'
        '    print(f"{role:<13}{sums[role] / counts[role]:>5.1f}")\n'
        'print("Name: token数, dtype: float64")\n'
        'top = max(sums, key=sums.get)\n'
        'print(f"消耗最多：{top}")\n'
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "groupby" in msg
