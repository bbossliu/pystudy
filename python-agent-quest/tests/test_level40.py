from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 40)


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


def test_too_few_asserts_fails():
    # 输出正确（1 条 assert 也能过迷你 runner），但断言不到 3 条
    code = (
        'def add(a, b):\n'
        '    return a + b\n'
        '\n'
        'def test_add():\n'
        '    assert add(1, 2) == 3\n'
        '\n'
        'for name, fn in list(globals().items()):\n'
        '    if name.startswith("test_") and callable(fn):\n'
        '        fn()\n'
        '        print(f"{name} 通过")\n'
    )
    lv = _level()
    r = run_code(code)
    assert "test_add 通过" in r.stdout  # 确认输出本身是对的，只卡在写法
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "assert" in msg
