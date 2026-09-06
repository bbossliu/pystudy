import os
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import server.chat as chat_mod
from server.main import app

client = TestClient(app)

DUMMY_KEY = "test-dummy-key-not-real"


def _clear_keys(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)


def _chat_payload(**overrides):
    payload = {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "level_id": 1,
        "code": "print('hi')",
        "question": "这关要做什么？",
    }
    payload.update(overrides)
    return payload


# ---- available_providers 的 env 过滤 ----


def test_available_providers_empty_when_no_keys(monkeypatch):
    _clear_keys(monkeypatch)
    assert chat_mod.available_providers() == []


def test_available_providers_deepseek_only(monkeypatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("DEEPSEEK_API_KEY", DUMMY_KEY)
    providers = chat_mod.available_providers()
    assert [p["id"] for p in providers] == ["deepseek"]
    assert providers[0]["models"] == ["deepseek-chat", "deepseek-reasoner"]


def test_available_providers_glm_only(monkeypatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("GLM_API_KEY", DUMMY_KEY)
    providers = chat_mod.available_providers()
    assert [p["id"] for p in providers] == ["glm"]
    assert providers[0]["models"] == ["glm-4.7", "glm-4.7-flash", "glm-4.5-air"]


def test_available_providers_both(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", DUMMY_KEY)
    monkeypatch.setenv("GLM_API_KEY", DUMMY_KEY)
    assert [p["id"] for p in chat_mod.available_providers()] == ["deepseek", "glm"]


# ---- GET /api/chat/providers ----


def test_providers_endpoint_returns_only_configured(monkeypatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("GLM_API_KEY", DUMMY_KEY)
    resp = client.get("/api/chat/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert [p["id"] for p in data] == ["glm"]
    assert DUMMY_KEY not in resp.text


# ---- POST /api/chat 校验 ----


def test_chat_rejects_unknown_provider(monkeypatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("DEEPSEEK_API_KEY", DUMMY_KEY)
    resp = client.post("/api/chat", json=_chat_payload(provider="openai"))
    assert resp.status_code == 400


def test_chat_rejects_unknown_model(monkeypatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("DEEPSEEK_API_KEY", DUMMY_KEY)
    resp = client.post("/api/chat", json=_chat_payload(model="gpt-4o"))
    assert resp.status_code == 400
    assert "模型" in resp.json()["detail"]


def test_chat_rejects_unknown_level(monkeypatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("DEEPSEEK_API_KEY", DUMMY_KEY)
    resp = client.post("/api/chat", json=_chat_payload(level_id=999))
    assert resp.status_code == 400


def test_chat_rejects_provider_without_key(monkeypatch):
    _clear_keys(monkeypatch)
    resp = client.post("/api/chat", json=_chat_payload())
    assert resp.status_code == 400
    assert "key" in resp.json()["detail"].lower()


# ---- 成功路径（mock openai client） ----


def _fake_openai(captured, reply="这是助教的固定回答", error=None):
    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            if error is not None:
                raise error
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=reply))]
            )

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs
            self.chat = SimpleNamespace(completions=FakeCompletions())

    return FakeClient


def test_chat_success(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", DUMMY_KEY)
    captured = {}
    monkeypatch.setattr(chat_mod, "OpenAI", _fake_openai(captured))
    resp = client.post("/api/chat", json=_chat_payload(code="name = '小K'"))
    assert resp.status_code == 200
    assert resp.json()["reply"] == "这是助教的固定回答"
    # system prompt 里包含关卡标题和学生当前代码
    messages = captured["messages"]
    assert messages[0]["role"] == "system"
    assert "变量与 f-string" in messages[0]["content"]
    assert "name = '小K'" in messages[0]["content"]
    assert messages[-1] == {"role": "user", "content": "这关要做什么？"}
    # key 只传给 SDK，绝不出现在响应里
    assert captured["client_kwargs"]["api_key"] == DUMMY_KEY
    assert DUMMY_KEY not in resp.text


def test_chat_success_glm_uses_glm_base_url(monkeypatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("GLM_API_KEY", DUMMY_KEY)
    captured = {}
    monkeypatch.setattr(chat_mod, "OpenAI", _fake_openai(captured))
    resp = client.post("/api/chat", json=_chat_payload(provider="glm", model="glm-4.7"))
    assert resp.status_code == 200
    assert captured["client_kwargs"]["base_url"] == "https://open.bigmodel.cn/api/paas/v4"
    assert captured["model"] == "glm-4.7"


def test_chat_truncates_long_code_in_system_prompt(monkeypatch):
    # 学生代码注入 system prompt 前必须截断，防超长代码打爆 token
    monkeypatch.setenv("DEEPSEEK_API_KEY", DUMMY_KEY)
    captured = {}
    monkeypatch.setattr(chat_mod, "OpenAI", _fake_openai(captured))
    long_code = "a = 1\n" * 2000  # 12000 字符，远超 4000 上限
    resp = client.post("/api/chat", json=_chat_payload(code=long_code))
    assert resp.status_code == 200
    system = captured["messages"][0]["content"]
    assert long_code not in system
    assert long_code[:4000] in system


# ---- API 报错路径 ----


def test_chat_api_error_returns_502(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", DUMMY_KEY)
    captured = {}
    monkeypatch.setattr(
        chat_mod, "OpenAI", _fake_openai(captured, error=RuntimeError("boom"))
    )
    resp = client.post("/api/chat", json=_chat_payload())
    assert resp.status_code == 502
    assert "出错" in resp.json()["detail"]
    assert DUMMY_KEY not in resp.text


def test_chat_401_hint_key_problem(monkeypatch):
    import httpx
    from openai import AuthenticationError

    monkeypatch.setenv("DEEPSEEK_API_KEY", DUMMY_KEY)
    request = httpx.Request("POST", "https://api.deepseek.com/chat/completions")
    error = AuthenticationError(
        "invalid api key", response=httpx.Response(401, request=request), body=None
    )
    captured = {}
    monkeypatch.setattr(chat_mod, "OpenAI", _fake_openai(captured, error=error))
    resp = client.post("/api/chat", json=_chat_payload())
    assert resp.status_code == 502
    detail = resp.json()["detail"]
    assert "401" in detail
    assert "key" in detail.lower()
    assert DUMMY_KEY not in resp.text


# ---- 真实调用（无 key 时跳过） ----


@pytest.mark.skipif(not os.environ.get("DEEPSEEK_API_KEY"), reason="需要 DEEPSEEK_API_KEY")
def test_chat_real_deepseek():
    resp = client.post(
        "/api/chat",
        json=_chat_payload(question="用一句话回答：print 是函数还是关键字？"),
    )
    assert resp.status_code == 200
    assert resp.json()["reply"]
