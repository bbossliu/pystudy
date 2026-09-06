from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 37)


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


def test_alias_and_shallow_copy_fail():
    # 输出正确（打印值硬编码对齐），但复制方式不对：
    # b = a 是引用赋值；a.copy() / a[:] 是浅拷贝——都必须拒，只有 deepcopy 过
    template = (
        'import copy\n'
        'a = [[1, 2], [3, 4]]\n'
        'b = {assign}\n'
        'b[0][0] = 99\n'
        'print("原件：1")\n'
        'print("副本：99")\n'
    )
    lv = _level()
    for assign in ("a", "a.copy()", "a[:]"):
        code = template.format(assign=assign)
        r = run_code(code)
        assert "原件：1" in r.stdout  # 确认输出本身是对的，只卡在写法
        passed, msg = lv.judge(code, r)
        assert not passed, f"{assign} 居然过了"
        assert "deepcopy" in msg
