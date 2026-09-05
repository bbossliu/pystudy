import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.request

import pytest

# 本机 shell 常配置 http_proxy/https_proxy/all_proxy：
# - urllib/httpx 会把本地回环请求错误地转发到代理（健康检查、stagehand 本地 SEA）
# - httpx 看到 socks5 的 all_proxy 还会因缺少 socksio 直接报错
# DeepSeek API 可直连，因此测试进程内直接移除代理变量（子进程 SEA 随之继承）
for _var in ("http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
    os.environ.pop(_var, None)

BASE = "http://127.0.0.1:8124"

pytestmark = pytest.mark.skipif(
    not os.environ.get("DEEPSEEK_API_KEY"),
    reason="需要 DEEPSEEK_API_KEY 环境变量",
)


@pytest.fixture(scope="module")
def server():
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server.main:app", "--port", "8124"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        try:
            urllib.request.urlopen(BASE + "/api/health", timeout=1)
            break
        except Exception:
            time.sleep(0.2)
    else:
        proc.terminate()
        pytest.fail("服务启动失败")
    yield proc
    proc.terminate()


def test_stagehand_level1_pass(server):
    asyncio.run(_run_level1_pass())


async def _run_level1_pass():
    from playwright.async_api import async_playwright
    from stagehand import AsyncStagehand

    from server.levels.loader import load_levels

    solution = load_levels()[0].solution

    client = AsyncStagehand(
        server="local",
        model_api_key=os.environ["DEEPSEEK_API_KEY"],
        local_ready_timeout_s=60,
    )
    session = None
    try:
        # SEA 本地模式要求显式给出浏览器启动参数，复用 playwright 已装的 chromium
        chrome_path = None
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as pw:
                chrome_path = pw.chromium.executable_path
        except Exception:
            pass
        launch_options = {"headless": True}
        if chrome_path:
            launch_options["executablePath"] = chrome_path

        session = await client.sessions.start(
            model_name="deepseek/deepseek-chat",
            browser={"type": "local", "launchOptions": launch_options},
            timeout=120,
        )
        assert session.data.cdp_url, "未拿到 CDP 地址"

        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(session.data.cdp_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()

            # 确定性步骤：直接注入第 1 关标准答案，不走 AI
            await page.goto(BASE)
            await page.wait_for_selector("#level-title")
            await page.evaluate(f"editor.setValue({json.dumps(solution)})")

            # AI 步骤：点击运行按钮（LLM 调用较慢，给足超时）
            act_resp = await session.act(input="点击运行按钮", page=page, timeout=180)
            assert act_resp.success

            # 确定性等待：代码执行有耗时，等过关提示出现后再让 AI 提取，
            # 避免 extract 抢跑读到空结果
            await page.wait_for_selector("#message.pass", timeout=15000)

            # AI 步骤：提取过关提示
            ext = await session.extract(
                instruction="提取页面上结果提示区域（#message 元素）的文本内容",
                schema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "结果提示区域的完整文本",
                        }
                    },
                    "required": ["message"],
                },
                page=page,
                timeout=180,
            )
            assert ext.success
            assert "过关" in ext.data.result["message"]
    finally:
        if session is not None:
            try:
                await session.end()
            except Exception:
                pass
        await client.close()
