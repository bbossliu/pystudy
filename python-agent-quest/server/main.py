import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from openai import AuthenticationError
from pydantic import BaseModel

from server.chat import PROVIDERS, available_providers, chat, configured_provider
from server.levels.loader import load_levels
from server.runner import run_code

app = FastAPI()
LEVELS = {lv.id: lv for lv in load_levels()}

STATIC_INDEX = Path(__file__).parent.parent / "static" / "index.html"


class RunRequest(BaseModel):
    level_id: int
    code: str


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/levels")
def list_levels():
    return [
        {
            "id": lv.id,
            "title": lv.title,
            "story": lv.story,
            "knowledge": lv.knowledge,
            "starter_code": lv.starter_code,
            "diagram": lv.diagram,
        }
        for lv in sorted(LEVELS.values(), key=lambda l: l.id)
    ]


@app.post("/api/run")
def run(req: RunRequest):
    lv = LEVELS.get(req.level_id)
    if lv is None:
        raise HTTPException(status_code=404, detail="关卡不存在")
    result = run_code(req.code, timeout=lv.timeout)
    try:
        if result.timed_out:
            return {
                "passed": False,
                "stdout": "",
                "stderr": "",
                "message": f"运行超时（超过 {lv.timeout} 秒），检查是不是有死循环？",
            }
        passed, message = lv.judge(req.code, result)
        return {
            "passed": passed,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "message": message,
        }
    finally:
        shutil.rmtree(result.workdir, ignore_errors=True)


@app.get("/")
def index():
    return FileResponse(STATIC_INDEX)


class ChatRequest(BaseModel):
    provider: str
    model: str
    level_id: int
    code: str
    question: str


@app.get("/api/chat/providers")
def chat_providers():
    return available_providers()


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    lv = LEVELS.get(req.level_id)
    if lv is None:
        raise HTTPException(status_code=400, detail="关卡不存在，刷新页面重试")
    cfg = PROVIDERS.get(req.provider)
    if cfg is None:
        raise HTTPException(status_code=400, detail=f"未知的提供商：{req.provider}")
    if configured_provider(req.provider) is None:
        raise HTTPException(
            status_code=400,
            detail=f"提供商 {cfg['name']} 未配置 API key，先在服务端环境变量 {cfg['env_key']} 里配置",
        )
    if req.model not in cfg["models"]:
        raise HTTPException(status_code=400, detail=f"未知的模型：{req.model}")
    try:
        reply = chat(req.provider, req.model, lv, req.code, req.question)
    except AuthenticationError:
        # 401 特判：不转发原始报错，避免任何 key 相关的信息泄进响应
        raise HTTPException(
            status_code=502,
            detail="模型服务返回 401：API key 可能不对或已过期，检查服务端环境变量里的 key",
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="调用模型服务出错了，稍后再试一次；如果一直失败，检查服务端网络和环境",
        )
    return {"reply": reply}
