import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

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
        }
        for lv in sorted(LEVELS.values(), key=lambda l: l.id)
    ]


@app.post("/api/run")
def run(req: RunRequest):
    lv = LEVELS.get(req.level_id)
    if lv is None:
        raise HTTPException(status_code=404, detail="关卡不存在")
    result = run_code(req.code)
    try:
        if result.timed_out:
            return {
                "passed": False,
                "stdout": "",
                "stderr": "",
                "message": "运行超时（超过 5 秒），检查是不是有死循环？",
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
