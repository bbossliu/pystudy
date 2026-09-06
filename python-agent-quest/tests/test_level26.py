from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 26)


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


def test_no_sort_fails():
    # 输出正确，但靠注册顺序碰巧排对，assemble 里没有排序——不满足写法要求
    code = (
        "class PromptAssembler:\n"
        "    def __init__(self):\n"
        "        self.sections = []\n"
        "\n"
        "    def section(self, name, text, order):\n"
        "        self.sections.append({\"name\": name, \"text\": text, \"order\": order})\n"
        "\n"
        "    def assemble(self):\n"
        "        return \"\\n\\n\".join(s[\"text\"] for s in self.sections)\n"
        "\n"
        "assembler = PromptAssembler()\n"
        "assembler.section(\"风格\", \"回答要简短。\", 0)\n"
        "assembler.section(\"身份\", \"你是小K。\", 1)\n"
        "assembler.section(\"工具\", \"可用工具：search\", 2)\n"
        "print(assembler.assemble())\n"
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "排序" in msg
