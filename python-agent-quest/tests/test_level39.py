from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 39)


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


def test_os_listdir_fails():
    # 输出正确，但用 os.listdir 字符串过滤——没用 pathlib 的 Path.glob
    code = (
        'import os\n'
        'open("a.json", "w").close()\n'
        'open("b.json", "w").close()\n'
        'open("c.txt", "w").close()\n'
        'for f in sorted(os.listdir(".")):\n'
        '    if f.endswith(".json"):\n'
        '        print(f)\n'
    )
    lv = _level()
    r = run_code(code)
    assert "a.json" in r.stdout  # 确认输出本身是对的，只卡在写法
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "Path" in msg
