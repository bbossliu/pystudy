from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 38)


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


def test_return_list_fails():
    # 输出正确，但函数 return 整个列表——一次性给全部，不是生成器
    code = (
        'def read_logs():\n'
        '    return ["日志1", "日志2", "日志3"]\n'
        '\n'
        'for log in read_logs():\n'
        '    print(f"读到：{log}")\n'
    )
    lv = _level()
    r = run_code(code)
    assert "读到：日志1" in r.stdout  # 确认输出本身是对的，只卡在写法
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "yield" in msg
