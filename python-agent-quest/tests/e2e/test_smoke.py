import json
import subprocess
import sys
import time
import urllib.request

import pytest
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8123"


@pytest.fixture(scope="module")
def server():
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server.main:app", "--port", "8123"],
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


def test_level1_pass_flow(server):
    from server.levels.loader import load_levels

    solution = load_levels()[0].solution
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE)
        page.wait_for_selector("#level-title")
        page.evaluate(f"editor.setValue({json.dumps(solution)})")
        page.click("#run-btn")
        page.wait_for_selector("#message.pass", timeout=10000)
        assert "过关" in page.inner_text("#message")
        browser.close()
