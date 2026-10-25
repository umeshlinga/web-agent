"""Browser agent core: observe -> act -> verify -> recover.

The agent grounds task targets semantically (role + text/label/name) in a
fresh DOM snapshot before every step. When an action or a verification
fails it can *recover* (recovery ON):

  * re-ground the target with fallback strategies (structural match:
    the submit control of the named form/container, partial-text match),
  * dismiss a blocking overlay via its dismiss control,
  * retry within a small budget (MAX_RETRIES).

With recovery OFF none of that happens: the first failure ends the task.
That ablation is what the eval measures. Every failure and recovery is
written to a JSONL run log.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

from .snapshot import Snapshot

ACTION_TIMEOUT_MS = 3000
VERIFY_TIMEOUT_S = 2.0
MAX_RETRIES = 2

DISMISS_TEXTS = {"×", "x", "close", "accept", "accept all", "dismiss",
                 "got it", "ok", "no thanks"}


@dataclass
class Target:
    """Semantic description of the element a step acts on."""
    role: str                       # button | link | textbox | combobox | checkbox | radio
    text: str = ""                  # visible text (buttons, links)
    label: str = ""                 # <label> text (form fields)
    name: str = ""                  # name attribute
    form: str = ""                  # enclosing form/container id (fallback hint)
    kind: str = ""                  # e.g. "submit" (structural fallback hint)


@dataclass
class Step:
    action: str                     # click | fill | select | check
    target: Target
    value: str = ""
    verify: object = None           # callable(page) -> bool, or None


@dataclass
class Task:
    name: str
    fixture: str                    # file name under fixtures/
    steps: list
    adversarial: bool = False
    description: str = ""


@dataclass
class TaskResult:
    task: str
    success: bool = False
    steps_completed: int = 0
    attempts: int = 0
    recoveries: int = 0
    error: str = ""


class RunLog:
    def __init__(self, path: str):
        self.path = path
        self._fh = open(path, "a", encoding="utf-8")

    def write(self, task: str, event: str, **kw) -> None:
        rec = {"ts": round(time.time(), 3), "task": task, "event": event}
        rec.update(kw)
        self._fh.write(json.dumps(rec) + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


def _role_matches(rec: dict, role: str) -> bool:
    tag, typ = rec["tag"], rec["type"]
    if role == "button":
        return tag == "button" or rec["role"] == "button" or \
            (tag == "input" and typ in ("submit", "button"))
    if role == "link":
        return tag == "a"
    if role == "textbox":
        return tag == "textarea" or (tag == "input" and typ in
                                     ("", "text", "password", "email", "search"))
    if role == "combobox":
        return tag == "select"
    if role == "checkbox":
        return tag == "input" and typ == "checkbox"
    if role == "radio":
        return tag == "input" and typ == "radio"
    return False


class Agent:
    def __init__(self, page, recovery: bool = True, log: RunLog | None = None):
        self.page = page
        self.recovery = recovery
        self.log = log

    # -- observation / grounding -------------------------------------------
    def _find_exact(self, snap: Snapshot, t: Target) -> dict | None:
        """Exact semantic match: text/label/name must match as specified."""
        best = None
        for rec in snap.elements:
            if not rec["visible"] or rec["disabled"]:
                continue
            if not _role_matches(rec, t.role):
                continue
            score = 1
            if t.text:
                if rec["text"] == t.text:
                    score = 100
                elif t.text.lower() in rec["text"].lower():
                    score = 50
                else:
                    continue
            if t.label:
                if rec["label"] == t.label:
                    score = max(score, 100)
                else:
                    continue
            if t.name:
                if rec["name"] == t.name:
                    score = max(score, 100)
                else:
                    continue
            if best is None or score > best[0]:
                best = (score, rec)
        return best[1] if best else None

    def _find_fallback(self, snap: Snapshot, t: Target) -> dict | None:
        """Re-grounding strategies used only in recovery: the target may
        have been renamed or moved, so fall back to structure."""
        cands = [r for r in snap.elements
                 if r["visible"] and not r["disabled"] and _role_matches(r, t.role)]
        if t.form:
            in_scope = [r for r in cands
                        if r["form"] == t.form or t.form in r.get("ancestors", [])]
            if t.kind == "submit":
                subs = [r for r in in_scope
                        if r["type"] == "submit" or r["tag"] == "button"]
                if len(subs) == 1:
                    return subs[0]
            if len(in_scope) == 1:
                return in_scope[0]
            if in_scope:
                cands = in_scope
        # last resort: a single visible candidate of that role on the page
        if len(cands) == 1:
            return cands[0]
        return None

    # -- action -------------------------------------------------------------
    def _act(self, rec: dict, step: Step) -> None:
        recipe = rec["recipe"]
        if not recipe:
            raise RuntimeError(f"no locator recipe for {rec['ref']}")
        loc = self.page.locator(recipe).first
        if step.action == "click":
            loc.click(timeout=ACTION_TIMEOUT_MS)
        elif step.action == "fill":
            loc.fill(step.value, timeout=ACTION_TIMEOUT_MS)
        elif step.action == "select":
            loc.select_option(step.value, timeout=ACTION_TIMEOUT_MS)
        elif step.action == "check":
            loc.check(timeout=ACTION_TIMEOUT_MS)
        else:
            raise ValueError(f"unknown action {step.action}")

    def _dismiss_overlay(self, task_name: str) -> bool:
        snap = Snapshot.take(self.page)
        for rec in snap.elements:
            if not rec["visible"] or rec["disabled"] or not rec["recipe"]:
                continue
            if _role_matches(rec, "button") and \
                    rec["text"].strip().lower() in DISMISS_TEXTS:
                try:
                    self.page.locator(rec["recipe"]).first.click(timeout=1500)
                    if self.log:
                        self.log.write(task_name, "recovery",
                                       kind="dismiss_overlay",
                                       control=rec["text"])
                    return True
                except Exception:
                    pass
        return False

    def _verify(self, step: Step) -> bool:
        if step.verify is None:
            return True
        deadline = time.time() + VERIFY_TIMEOUT_S
        while True:
            try:
                if step.verify(self.page):
                    return True
            except Exception:
                pass
            if time.time() >= deadline:
                return False
            time.sleep(0.1)

    # -- the loop -------------------------------------------------------------
    def run_task(self, task: Task) -> TaskResult:
        res = TaskResult(task=task.name)
        for idx, step in enumerate(task.steps, start=1):
            ok = self._run_step(task, idx, step, res)
            if not ok:
                res.error = res.error or f"step {idx} failed"
                return res
            res.steps_completed += 1
        res.success = True
        if self.log:
            self.log.write(task.name, "task_success",
                           attempts=res.attempts, recoveries=res.recoveries)
        return res

    def _run_step(self, task: Task, idx: int, step: Step,
                  res: TaskResult) -> bool:
        retries_left = MAX_RETRIES if self.recovery else 0
        reground = False
        while True:
            res.attempts += 1
            snap = Snapshot.take(self.page)
            if self.log:
                self.log.write(task.name, "observe", step=idx,
                               elements=len(snap))
            rec = self._find_fallback(snap, step.target) if reground \
                else self._find_exact(snap, step.target)
            failure = None
            failure_full = ""
            if rec is None:
                failure = "target_not_found"
            else:
                try:
                    self._act(rec, step)
                except Exception as exc:  # timeout, intercept, stale, ...
                    failure_full = str(exc)
                    failure = f"action_error: {failure_full.splitlines()[0][:160]}"
                else:
                    if self._verify(step):
                        if self.log:
                            self.log.write(task.name, "step_ok", step=idx,
                                           ref=rec["ref"])
                        return True
                    failure = "verify_failed"
            if self.log:
                self.log.write(task.name, "failure", step=idx, reason=failure,
                               recovery=self.recovery)
            if not self.recovery or retries_left <= 0:
                res.error = f"step {idx}: {failure}"
                return False
            # --- recovery ---
            retries_left -= 1
            res.recoveries += 1
            if "intercepts pointer events" in failure_full:
                self._dismiss_overlay(task.name)
            reground = True
            if self.log:
                self.log.write(task.name, "recovery", step=idx,
                               kind="reground_retry")
