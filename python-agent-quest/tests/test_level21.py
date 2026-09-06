from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 21)


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


def test_hardcoded_index_fails():
    # 输出正确，但 discover_skills 直接返回写死的索引——没有遍历也没有解析
    code = (
        "SKILLS_FS = {\n"
        "    \"weather/SKILL.md\": \"---\\nname: 查天气\\ndesc: 查询城市天气\\n---\\n正文略\",\n"
        "    \"stock/SKILL.md\": \"---\\nname: 查股票\\ndesc: 查询股票价格\\n---\\n正文略\",\n"
        "}\n"
        "\n"
        "def discover_skills(fs):\n"
        "    return [\"- 查天气: 查询城市天气\", \"- 查股票: 查询股票价格\"]\n"
        "\n"
        "print(\"可用技能：\")\n"
        "for line in discover_skills(SKILLS_FS):\n"
        "    print(line)\n"
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "循环" in msg or "遍历" in msg
