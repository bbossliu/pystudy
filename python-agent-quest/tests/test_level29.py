from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 29)


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
    # 输出正确，但用纯 Python 循环算统计——没有用 numpy 向量化
    code = (
        "latencies = [120, 85, 340, 90, 1500, 200, 95]\n"
        "total = 0\n"
        "for x in latencies:\n"
        "    total += x\n"
        "mean = total / len(latencies)\n"
        "best = 0\n"
        "for x in latencies:\n"
        "    if x + 100 > best:\n"
        "        best = x + 100\n"
        'print(f"均值：{mean:.1f}")\n'
        'print(f"修正后最大值：{best}")\n'
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "np.array" in msg
