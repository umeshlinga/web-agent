# browser-agent-lab

A small, working **browser agent with failure recovery**, built by
Umesh Linga as a portfolio/research project. It drives headless Chromium
(Playwright) through a suite of local HTML tasks using an
**observe → act → verify → recover** loop, and it measures — with an
ablation, not adjectives — what the recovery half of that loop is worth.

> Honest scope: this is a research/portfolio system that runs against
> deterministic local fixture pages in headless Chromium. It is not a
> product, it is not deployed anywhere, and it does not browse the live
> web. Every number in `RESULTS.md` is generated from the raw run files
> in `results/` — nothing is hand-entered.

## Why this exists

Locating an element once and replaying fixed locators breaks the moment
a page changes under the agent: a button gets renamed, an element moves,
an overlay intercepts the click. This project isolates that failure mode
with nine deliberately adversarial fixtures and a recovery mechanism,
then runs the same suite with recovery switched off to show the
difference.

## Architecture

```
        ┌──────────────────────────────────────────────┐
        │  for each step of a task                     │
        │                                              │
        │   OBSERVE   fresh DOM snapshot: every        │
        │             interactive element with a ref   │
        │             (e1, e2, …), role, text, id,     │
        │             name, label, form, visibility    │
        │        ↓                                     │
        │   GROUND    match the step's semantic target │
        │             (role + text / label / name)     │
        │        ↓                                     │
        │   ACT       click / fill / select / check    │
        │             via the element's locator recipe │
        │        ↓                                     │
        │   VERIFY    check the step's postcondition   │
        │             (visible text, row counts,       │
        │             field values, checked state)     │
        │        ↓  on any failure                     │
        │   RECOVER   (recovery ON only) re-ground,    │
        │             dismiss overlay, retry ≤ 2       │
        └──────────────────────────────────────────────┘
```

- `src/snapshot.py` — page observation. Injects JS that enumerates
  interactive elements and records their semantic attributes plus a
  locator recipe (id → name → text → placeholder).
- `src/agent.py` — the loop. `Target`/`Step`/`Task` definitions,
  exact semantic grounding, fallback (structural) re-grounding, overlay
  dismissal, retry budget, and a JSONL run log (`logs/`) recording every
  observe, failure and recovery.
- `src/tasks.py` — the 30-task suite; every step carries an explicit
  postcondition written against the page.
- `fixtures/` — the deterministic local pages (served via `file://`).
- `scripts/run_eval.py` — runs the suite with recovery ON and OFF,
  writes `results/run_on.json` / `results/run_off.json`, and generates
  `RESULTS.md` from them.

## How recovery works

When a step fails — target not found, action error (timeout, stale
element, click intercepted), or postcondition not met — recovery does
three things, each logged:

1. **Re-ground.** The target is looked up again in a fresh snapshot with
   fallback strategies instead of the exact text/id: e.g. *the* submit
   control of the named form/container, or the only visible element of
   that role in scope. This survives the element being renamed
   ("Pay now" → "Confirm payment", new id) or moved in the DOM.
2. **Dismiss overlays.** If the click error says another element
   *intercepts pointer events*, the agent finds the overlay's dismiss
   control (Accept / Close / × …), clicks it, then retries.
3. **Retry within a budget.** At most 2 retries per step; then the task
   fails and the failure is reported as-is.

Recovery OFF (`--mode off`, or `BROWSER_AGENT_RECOVERY=off`) disables
all three: no re-grounding, no dismissal, no retries — the first failure
ends the task. That is the ablation the results report.

## The task suite

Twenty-one ordinary tasks act as controls: a competent agent should
pass them with or without recovery. They cover three-stage checkouts,
forms that reject invalid input and must be corrected, wizards with a
back step, dependent dropdowns and toggle-revealed fields, paginated
tables with combined sort + filter, inline row editing, tabbed and
accordion layouts, stacked modals, a date-picker grid, an autocomplete,
delayed rendering, and a segmented code entry. Nine tasks are
adversarial — the page mutates or obstructs mid-task:

- **`adversarial_label_change`** — after the card field is first typed
  into, the pay button is renamed (`#pay-btn`/"Pay now" →
  `#confirm-btn-x7`/"Confirm payment") and moved below the summary.
- **`adversarial_overlay_move`** — enabling advanced settings replaces
  the Save button (new id, new label, far down the page) while a fixed
  cookie overlay covers the lower viewport and intercepts its clicks.
- **`adversarial_double_label_change`** — the form's call-to-action is
  renamed twice in one task, once per field typed into.
- **`adversarial_moved_button`** — an unrelated checkbox re-renders
  the action bar: the working Checkout button moves into the order
  summary, and the toolbar keeps a stale same-label decoy.
- **`adversarial_banner_reappears`** — a dismissed promo banner comes
  back when a field is typed into, covering the Save button again.
- **`adversarial_late_overlay`** — the Confirm button never changes;
  a full-screen promo overlay raised by the previous click covers it.
- **`adversarial_renamed_field`** — choosing a country renames a
  field's label ("ZIP code" → "Postal code") mid-task.
- **`adversarial_decoy_button`** — opting into partner offers inserts
  a same-label "Subscribe" decoy above the real form.
- **`adversarial_rename_under_overlay`** — typing a card number
  renames the pay button and raises a cookie bar over it at the same
  time; recovery must re-ground *and* dismiss, in sequence.

Latest measured outcome (regenerate with the eval; see `RESULTS.md`):
recovery ON passed all 30 tasks; recovery OFF passed the 21 controls
and failed all nine adversarial tasks — renamed targets were never
found, covered buttons' clicks timed out, and decoys failed their
postconditions. Seven adversarial tasks needed exactly one recovery
with recovery ON; the two double-mutation tasks needed two.

## Setup

Exact commands used to set this up (Python 3.12):

```bash
python3 -m venv .venv
.venv/bin/pip install playwright        # or: .venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium   # downloads headless Chromium
.venv/bin/pip install pytest            # for the smoke test (in requirements.txt)
```

## Run

```bash
.venv/bin/python scripts/run_eval.py            # both modes + RESULTS.md
.venv/bin/python scripts/run_eval.py --mode on  # recovery ON only
.venv/bin/python -m pytest tests/               # smoke test (login task)
```

Outputs: `results/run_on.json`, `results/run_off.json`,
`logs/run_on.jsonl`, `logs/run_off.jsonl`, `RESULTS.md`.
See `DEMO.md` for a real run transcript excerpt.

## Layout

```
src/         agent loop, snapshot, task definitions
fixtures/    30 deterministic local HTML pages
scripts/     run_eval.py — ON/OFF evaluation runner
tests/       smoke test
results/     raw run output (JSON)
logs/        JSONL run logs (failures + recoveries)
```
