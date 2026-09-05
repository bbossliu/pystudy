from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 22)


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


def test_no_closure_fails():
    # 输出正确，但 create_my_deep_agent 直接处理请求、不返回闭包——不满足写法要求
    code = (
        "def call_model(request):\n"
        "    return \"LLM 回复\"\n"
        "\n"
        "class Middleware:\n"
        "    def wrap_model_call(self, request, handler):\n"
        "        return handler(request)\n"
        "\n"
        "class LogMiddleware(Middleware):\n"
        "    def wrap_model_call(self, request, handler):\n"
        "        print(\">> 进入 LogMiddleware\")\n"
        "        result = handler(request)\n"
        "        print(\"<< 离开 LogMiddleware\")\n"
        "        return result\n"
        "\n"
        "def run_with_middleware(request, middlewares):\n"
        "    handler = call_model\n"
        "    for mw in reversed(middlewares):\n"
        "        inner = handler\n"
        "        handler = lambda req, mw=mw, inner=inner: mw.wrap_model_call(req, inner)\n"
        "    return handler(request)\n"
        "\n"
        "def create_my_deep_agent(middlewares, request):\n"
        "    print(f\"装配了 {len(middlewares)} 个中间件\")\n"
        "    return run_with_middleware(request, middlewares)\n"
        "\n"
        "result = create_my_deep_agent([LogMiddleware(), LogMiddleware()], \"你好\")\n"
        "print(result)\n"
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "闭包" in msg
