import importlib
import pkgutil
from dataclasses import dataclass
from typing import Callable

from server.runner import RunResult

JudgeFn = Callable[[str, RunResult], "tuple[bool, str]"]

REQUIRED_ATTRS = ["ID", "TITLE", "STORY", "KNOWLEDGE", "STARTER_CODE", "SOLUTION", "judge"]


DEFAULT_TIMEOUT = 5


@dataclass
class Level:
    id: int
    title: str
    story: str
    knowledge: str
    starter_code: str
    solution: str
    judge: JudgeFn
    timeout: int = DEFAULT_TIMEOUT


def load_levels() -> list[Level]:
    import server.levels as pkg

    levels = []
    for info in pkgutil.iter_modules(pkg.__path__):
        if not info.name.startswith("level"):
            continue
        mod = importlib.import_module(f"server.levels.{info.name}")
        for attr in REQUIRED_ATTRS:
            if not hasattr(mod, attr):
                raise ValueError(f"关卡模块 {info.name} 缺少字段 {attr}")
        levels.append(
            Level(mod.ID, mod.TITLE, mod.STORY, mod.KNOWLEDGE,
                  mod.STARTER_CODE, mod.SOLUTION, mod.judge,
                  getattr(mod, "TIMEOUT", DEFAULT_TIMEOUT))
        )
    return sorted(levels, key=lambda lv: lv.id)
