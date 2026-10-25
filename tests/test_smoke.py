"""Smoke test: the agent completes the simplest task (login) end to end."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright  # noqa: E402

from src.agent import Agent  # noqa: E402
from src.tasks import TASKS  # noqa: E402

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_login_task_end_to_end():
    task = next(t for t in TASKS if t.name == "login")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto((FIXTURES / task.fixture).as_uri())
        result = Agent(page, recovery=True).run_task(task)
        browser.close()
    assert result.success, f"login task failed: {result.error}"
    assert result.steps_completed == len(task.steps)
