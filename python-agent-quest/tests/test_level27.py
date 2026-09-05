from server.levels.loader import load_levels
from server.runner import run_code


def _level():
    return next(lv for lv in load_levels() if lv.id == 27)


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


def test_wrong_order_fails():
    # 输出正确，但 append 先改内存队列再写事件日志——顺序反了，不满足写法要求
    code = (
        "class Inbox:\n"
        "    def __init__(self):\n"
        "        self.events = []\n"
        "        self.queue = []\n"
        "\n"
        "    def append(self, item):\n"
        "        self.queue.append(item)\n"
        "        self.events.append({\"op\": \"add\", \"item\": item})\n"
        "\n"
        "    def claim(self):\n"
        "        item = self.queue[0]\n"
        "        self.events.append({\"op\": \"remove\", \"item\": item})\n"
        "        self.queue.pop(0)\n"
        "        return item\n"
        "\n"
        "    @classmethod\n"
        "    def replay(cls, events):\n"
        "        inbox = cls()\n"
        "        for event in events:\n"
        "            if event[\"op\"] == \"add\":\n"
        "                inbox.queue.append(event[\"item\"])\n"
        "            elif event[\"op\"] == \"remove\":\n"
        "                inbox.queue.remove(event[\"item\"])\n"
        "        return inbox\n"
        "\n"
        "inbox = Inbox()\n"
        "inbox.append(\"消息1\")\n"
        "inbox.append(\"消息2\")\n"
        "inbox.claim()\n"
        "print(f\"当前队列：{inbox.queue}\")\n"
        "restored = Inbox.replay(inbox.events)\n"
        "print(f\"重放恢复：{restored.queue}\")\n"
    )
    lv = _level()
    r = run_code(code)
    passed, msg = lv.judge(code, r)
    assert not passed
    assert "顺序反了" in msg
