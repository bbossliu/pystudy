from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 30)


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


def test_pure_python_lists_fails():
    # 输出正确，但用纯 Python 嵌套列表手工拼——没有 reshape 和切片
    code = (
        "rows = [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]\n"
        'print("形状：(3, 4)")\n'
        'print("第 2 天：[" + " ".join(str(x) for x in rows[1]) + "]")\n'
        'print("时段 0：[" + " ".join(str(rows[i][0]) for i in range(3)) + "]")\n'
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "reshape" in msg
