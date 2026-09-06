import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass

DEFAULT_TIMEOUT = 5


@dataclass
class RunResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    workdir: str


def run_code(source: str, timeout: int = DEFAULT_TIMEOUT) -> RunResult:
    workdir = tempfile.mkdtemp(prefix="quest_")
    script = os.path.join(workdir, "main.py")
    with open(script, "w", encoding="utf-8") as f:
        f.write(source)
    try:
        proc = subprocess.run(
            [sys.executable, "main.py"],
            cwd=workdir,
            capture_output=True,
            encoding="utf-8",
            timeout=timeout,
        )
        return RunResult(proc.stdout, proc.stderr, proc.returncode, False, workdir)
    except subprocess.TimeoutExpired:
        return RunResult("", "运行超时", -1, True, workdir)
