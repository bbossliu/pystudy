import os

from openai import OpenAI

# 两个 provider 都是 OpenAI 兼容端点，统一用 openai SDK 调用；
# key 只从环境变量读，传给 SDK，绝不出现在响应和日志里
PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "env_key": "DEEPSEEK_API_KEY",
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
    "glm": {
        "name": "智谱 GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "env_key": "GLM_API_KEY",
        "models": ["glm-4.7", "glm-4.7-flash", "glm-4.5-air"],
    },
}

TIMEOUT = 60

SYSTEM_TEMPLATE = """\
你是「造一个 Agent」Python 闯关游戏的助教，学生是有 Java 基础的 Python 初学者。
用简洁的中文回答，示例代码用 Python，可以适当对比 Java 帮助理解。

当前关卡：第 {level_id} 关 · {title}

关卡剧情：
{story}

关卡知识卡：
{knowledge}

学生当前的代码：
```python
{code}
```

结合关卡内容和学生的代码回答问题。如果学生直接要通关答案，给提示和思路，不要贴完整答案。"""

# 学生代码注入 system prompt 前的长度上限，防超长代码打爆 token
CODE_MAX_CHARS = 4000


def available_providers() -> list[dict]:
    """只返回 env key 已配置的提供商。"""
    return [
        {"id": pid, "name": cfg["name"], "models": cfg["models"]}
        for pid, cfg in PROVIDERS.items()
        if os.environ.get(cfg["env_key"])
    ]


def configured_provider(provider_id: str) -> "dict | None":
    """provider 存在且 key 已配置时返回配置，否则返回 None。"""
    cfg = PROVIDERS.get(provider_id)
    if cfg and os.environ.get(cfg["env_key"]):
        return cfg
    return None


def build_system_prompt(level, code: str) -> str:
    return SYSTEM_TEMPLATE.format(
        level_id=level.id,
        title=level.title,
        story=level.story,
        knowledge=level.knowledge,
        code=code[:CODE_MAX_CHARS],
    )


def chat(provider_id: str, model: str, level, code: str, question: str) -> str:
    """单轮对话：system 带关卡上下文 + 学生代码，user 为学生的问题。"""
    cfg = PROVIDERS[provider_id]
    client = OpenAI(
        base_url=cfg["base_url"],
        api_key=os.environ.get(cfg["env_key"]),
        timeout=TIMEOUT,
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": build_system_prompt(level, code)},
            {"role": "user", "content": question},
        ],
    )
    return resp.choices[0].message.content
