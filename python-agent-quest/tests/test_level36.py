from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 36)


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


def test_manual_parsing_fails():
    # 输出正确，但用 find/切片手写解析——没有 re 正则
    code = (
        'text = "用户说：工单 GD-102938 很急，另外 GD-000415 也看下，谢谢"\n'
        'tickets = []\n'
        'i = 0\n'
        'while True:\n'
        '    i = text.find("GD-", i)\n'
        '    if i == -1:\n'
        '        break\n'
        '    tickets.append(text[i:i + 9])\n'
        '    i += 9\n'
        'print(tickets)\n'
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "re" in msg
