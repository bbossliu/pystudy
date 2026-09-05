from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 10)


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


def test_correct_output_without_decorator_fails():
    code = (
        "TOOL_REGISTRY = {}\n"
        "def search(query):\n"
        '    return f"搜索：{query}"\n'
        'TOOL_REGISTRY["search"] = search\n'
        'print(f"已注册工具：{list(TOOL_REGISTRY.keys())}")\n'
        'print(search("Python 教程"))\n'
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "装饰器" in msg
