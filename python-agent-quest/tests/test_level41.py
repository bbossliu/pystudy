from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 41)


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


def test_no_threads_fails():
    # 输出正确，但没起线程——直接往列表里塞答案
    code = (
        'results = ["线程A 完成", "线程B 完成"]\n'
        'for line in sorted(results):\n'
        '    print(line)\n'
    )
    lv = _level()
    r = run_code(code)
    assert "线程A 完成" in r.stdout  # 确认输出本身是对的，只卡在写法
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "Thread" in msg
