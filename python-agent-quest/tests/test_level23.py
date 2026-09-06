from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 23)


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


def test_no_class_fails():
    # 输出正确，但没有定义 ScopedLayers 类——不满足写法要求
    code = (
        'a_view = {"模型": "deepseek-chat", "温度": 0.1}\n'
        'b_view = {"模型": "deepseek-chat", "温度": 0.7}\n'
        'print(f"agent-A 的温度：{a_view[\'温度\']}")\n'
        'print(f"agent-B 的温度：{b_view[\'温度\']}")\n'
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "ScopedLayers" in msg
