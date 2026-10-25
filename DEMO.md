# Demo — a real run, from the logs

Everything below is copied from an actual evaluation run
(`logs/run_on.jsonl`, produced by `scripts/run_eval.py`). Nothing here
is a mock.

## Console output (recovery ON, then OFF)

```
[on] PASS login (attempts=3, recoveries=0)
[on] PASS table_filter (attempts=2, recoveries=0)
[on] PASS multistep_form (attempts=7, recoveries=0)
[on] PASS settings_form (attempts=4, recoveries=0)
[on] PASS todo_list (attempts=5, recoveries=0)
[on] PASS sort_table (attempts=1, recoveries=0)
[on] PASS adversarial_label_change (attempts=4, recoveries=1)
[on] PASS adversarial_overlay_move (attempts=4, recoveries=1)
[on] PASS checkout_full (attempts=11, recoveries=0)
[on] PASS validation_form (attempts=10, recoveries=0)
[on] PASS paginated_table (attempts=5, recoveries=0)
[on] PASS dependent_settings (attempts=6, recoveries=0)
[on] PASS stacked_modals (attempts=4, recoveries=0)
[on] PASS delayed_render (attempts=3, recoveries=0)
[on] PASS date_picker (attempts=2, recoveries=0)
[on] PASS autocomplete_select (attempts=2, recoveries=0)
[on] PASS wizard_backtrack (attempts=7, recoveries=0)
[on] PASS dependent_dropdowns (attempts=3, recoveries=0)
[on] PASS cart_update (attempts=3, recoveries=0)
[on] PASS tabbed_panels (attempts=6, recoveries=0)
[on] PASS accordion_form (attempts=7, recoveries=0)
[on] PASS inline_edit_table (attempts=3, recoveries=0)
[on] PASS otp_code_entry (attempts=5, recoveries=0)
[on] PASS adversarial_double_label_change (attempts=6, recoveries=2)
[on] PASS adversarial_moved_button (attempts=3, recoveries=1)
[on] PASS adversarial_banner_reappears (attempts=4, recoveries=1)
[on] PASS adversarial_late_overlay (attempts=3, recoveries=1)
[on] PASS adversarial_renamed_field (attempts=4, recoveries=1)
[on] PASS adversarial_decoy_button (attempts=4, recoveries=1)
[on] PASS adversarial_rename_under_overlay (attempts=5, recoveries=2)
[off] PASS login (attempts=3, recoveries=0)
[off] PASS table_filter (attempts=2, recoveries=0)
[off] PASS multistep_form (attempts=7, recoveries=0)
[off] PASS settings_form (attempts=4, recoveries=0)
[off] PASS todo_list (attempts=5, recoveries=0)
[off] PASS sort_table (attempts=1, recoveries=0)
[off] FAIL adversarial_label_change (attempts=3, recoveries=0) -- step 3: target_not_found
[off] FAIL adversarial_overlay_move (attempts=3, recoveries=0) -- step 3: action_error: Locator.click: Timeout 3000ms exceeded.
[off] PASS checkout_full (attempts=11, recoveries=0)
[off] PASS validation_form (attempts=10, recoveries=0)
[off] PASS paginated_table (attempts=5, recoveries=0)
[off] PASS dependent_settings (attempts=6, recoveries=0)
[off] PASS stacked_modals (attempts=4, recoveries=0)
[off] PASS delayed_render (attempts=3, recoveries=0)
[off] PASS date_picker (attempts=2, recoveries=0)
[off] PASS autocomplete_select (attempts=2, recoveries=0)
[off] PASS wizard_backtrack (attempts=7, recoveries=0)
[off] PASS dependent_dropdowns (attempts=3, recoveries=0)
[off] PASS cart_update (attempts=3, recoveries=0)
[off] PASS tabbed_panels (attempts=6, recoveries=0)
[off] PASS accordion_form (attempts=7, recoveries=0)
[off] PASS inline_edit_table (attempts=3, recoveries=0)
[off] PASS otp_code_entry (attempts=5, recoveries=0)
[off] FAIL adversarial_double_label_change (attempts=2, recoveries=0) -- step 2: target_not_found
[off] FAIL adversarial_moved_button (attempts=2, recoveries=0) -- step 2: verify_failed
[off] FAIL adversarial_banner_reappears (attempts=3, recoveries=0) -- step 3: action_error: Locator.click: Timeout 3000ms exceeded.
[off] FAIL adversarial_late_overlay (attempts=2, recoveries=0) -- step 2: action_error: Locator.click: Timeout 3000ms exceeded.
[off] FAIL adversarial_renamed_field (attempts=2, recoveries=0) -- step 2: target_not_found
[off] FAIL adversarial_decoy_button (attempts=3, recoveries=0) -- step 3: verify_failed
[off] FAIL adversarial_rename_under_overlay (attempts=3, recoveries=0) -- step 3: target_not_found
```

## The interesting part: two recoveries, as logged

**Renamed button** (`adversarial_label_change`, recovery ON). Steps 1–2
fill the checkout form; typing in the card field renames the pay button
mid-task. At step 3 the exact target ("Pay now") no longer exists, the
agent re-grounds structurally — the submit control of the `#checkout`
form — and finishes:

```
observe   step=3 elements=3
failure   step=3 reason=target_not_found
recovery  step=3 kind=reground_retry
observe   step=3 elements=3
step_ok   step=3 ref=e3
task_success attempts=4 recoveries=1
```

**Covered, relocated button** (`adversarial_overlay_move`, recovery ON).
The replacement Save button is found, but the cookie overlay intercepts
the click. The agent dismisses the overlay via its "Accept" control
(the next snapshot has 3 elements instead of 4 — the overlay is gone),
re-grounds, and clicks through:

```
observe   step=3 elements=4
failure   step=3 reason=action_error: Locator.click: Timeout 3000ms exceeded.
recovery  kind=dismiss_overlay control=Accept
recovery  step=3 kind=reground_retry
observe   step=3 elements=3
step_ok   step=3 ref=e3
task_success attempts=4 recoveries=1
```

With recovery OFF, both tasks stop at exactly these failures — see the
console output above and `results/run_off.json`.
