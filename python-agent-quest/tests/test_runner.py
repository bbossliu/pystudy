import os

from server.runner import run_code


def test_run_code_captures_stdout():
    r = run_code("print('hello')")
    assert r.stdout.strip() == "hello"
    assert r.exit_code == 0
    assert not r.timed_out


def test_run_code_timeout():
    r = run_code("while True: pass", timeout=1)
    assert r.timed_out


def test_run_code_stderr_on_error():
    r = run_code("raise ValueError('boom')")
    assert r.exit_code != 0
    assert "ValueError" in r.stderr


def test_run_code_can_write_files_in_workdir():
    r = run_code("open('a.txt', 'w').write('hi')")
    assert os.path.exists(os.path.join(r.workdir, "a.txt"))
