"""Task suite: 8 tasks over local fixture pages.

Every step carries an explicit postcondition (verify) written against the
page: visible text, row counts, element state. Two tasks are adversarial:
the page mutates mid-task so a locate-once / no-recovery agent fails.
"""
from __future__ import annotations

from .agent import Step, Target, Task


# -- postcondition helpers ---------------------------------------------------
def text_is(selector: str, expected: str):
    def check(page) -> bool:
        loc = page.locator(selector)
        return loc.count() > 0 and loc.first.inner_text().strip() == expected
    return check


def text_contains(selector: str, needle: str):
    def check(page) -> bool:
        loc = page.locator(selector)
        return loc.count() > 0 and needle in loc.first.inner_text()
    return check


def visible_rows(selector: str, n: int):
    def check(page) -> bool:
        return page.locator(f"{selector}:visible").count() == n
    return check


def first_cell_is(table_body: str, expected: str):
    def check(page) -> bool:
        row = page.locator(f"{table_body} tr").first
        return row.locator("td").first.inner_text().strip() == expected
    return check


def li_count_is(n: int, done: int):
    def check(page) -> bool:
        total = page.locator("#list li").count()
        marked = page.locator("#list li.done").count()
        return total == n and marked == done
    return check


def is_checked(selector: str):
    def check(page) -> bool:
        return page.locator(selector).first.is_checked()
    return check


def field_value_is(selector: str, expected: str):
    def check(page) -> bool:
        return page.locator(selector).first.input_value() == expected
    return check


TASKS: list[Task] = [
    Task(
        name="login",
        fixture="login.html",
        description="Fill a login form and submit it.",
        steps=[
            Step("fill", Target("textbox", label="Username"), "ada",
                 verify=field_value_is("#username", "ada")),
            Step("fill", Target("textbox", label="Password"), "s3cret",
                 verify=field_value_is("#password", "s3cret")),
            Step("click", Target("button", text="Sign in"),
                 verify=text_is("#banner", "Welcome, ada")),
        ],
    ),
    Task(
        name="table_filter",
        fixture="table_filter.html",
        description="Search and category-filter a table down to one row.",
        steps=[
            Step("fill", Target("textbox", label="Search"), "an",
                 verify=visible_rows("#items tr", 1)),
            Step("select", Target("combobox", label="Category"), "Fruit",
                 verify=visible_rows("#items tr", 1)),
        ],
    ),
    Task(
        name="multistep_form",
        fixture="multistep_form.html",
        description="Three-step account wizard with a review screen.",
        steps=[
            Step("fill", Target("textbox", label="Full name"), "Ada Lovelace",
                 verify=field_value_is("#fullname", "Ada Lovelace")),
            Step("fill", Target("textbox", label="Email"), "ada@example.com",
                 verify=field_value_is("#email", "ada@example.com")),
            Step("click", Target("button", text="Next"),
                 verify=lambda p: not p.locator("#step2").first.is_hidden()),
            Step("select", Target("combobox", label="Plan"), "Pro",
                 verify=field_value_is("#plan", "Pro")),
            Step("check", Target("checkbox", label="Email me product news"),
                 verify=is_checked("#newsletter")),
            Step("click", Target("button", text="Next"),
                 verify=text_contains("#review", "Ada Lovelace")),
            Step("click", Target("button", text="Create account"),
                 verify=text_is("#done",
                                "Account created for Ada Lovelace on the Pro plan")),
        ],
    ),
    Task(
        name="settings_form",
        fixture="settings.html",
        description="Selects, a checkbox and a radio group, then save.",
        steps=[
            Step("select", Target("combobox", label="Theme"), "Dark",
                 verify=field_value_is("#theme", "Dark")),
            Step("check", Target("checkbox", label="Enable notifications"),
                 verify=is_checked("#notify")),
            Step("check", Target("radio", label="Compact"),
                 verify=is_checked("#dens-compact")),
            Step("click", Target("button", text="Save settings"),
                 verify=text_is("#saved", "Settings saved")),
        ],
    ),
    Task(
        name="todo_list",
        fixture="todo.html",
        description="Add two items, mark the first one done.",
        steps=[
            Step("fill", Target("textbox", label="New item"), "Buy milk",
                 verify=field_value_is("#new-item", "Buy milk")),
            Step("click", Target("button", text="Add"),
                 verify=visible_rows("#list li", 1)),
            Step("fill", Target("textbox", label="New item"), "Read paper",
                 verify=field_value_is("#new-item", "Read paper")),
            Step("click", Target("button", text="Add"),
                 verify=visible_rows("#list li", 2)),
            Step("check", Target("checkbox", name="done-toggle"),
                 verify=li_count_is(2, 1)),
        ],
    ),
    Task(
        name="sort_table",
        fixture="sort_table.html",
        description="Sort a table by score, highest first.",
        steps=[
            Step("click", Target("button", text="Score"),
                 verify=first_cell_is("#rows", "Leo")),
        ],
    ),
    Task(
        name="adversarial_label_change",
        fixture="adversarial_label.html",
        adversarial=True,
        description="Checkout: the pay button is renamed and moved "
                    "after the card field is first typed into.",
        steps=[
            Step("fill", Target("textbox", label="Name on card"), "Ada Lovelace",
                 verify=field_value_is("#cc-name", "Ada Lovelace")),
            Step("fill", Target("textbox", label="Card number"), "4242",
                 verify=field_value_is("#cc-num", "4242")),
            Step("click",
                 Target("button", text="Pay now", form="checkout", kind="submit"),
                 verify=text_is("#success", "Payment confirmed")),
        ],
    ),
    Task(
        name="adversarial_overlay_move",
        fixture="adversarial_overlay.html",
        adversarial=True,
        description="Enabling advanced settings replaces the Save button "
                    "(new id/label, far down the page) while a fixed "
                    "cookie overlay intercepts clicks on it.",
        steps=[
            Step("check", Target("checkbox", label="Advanced settings"),
                 verify=is_checked("#advanced")),
            Step("select", Target("combobox", label="Log level"), "Verbose",
                 verify=field_value_is("#level", "Verbose")),
            Step("click",
                 Target("button", text="Save", form="panel", kind="submit"),
                 verify=text_is("#saved-msg", "Settings saved (level: Verbose)")),
        ],
    ),
]


# -- extra postcondition helpers (30-task suite) ------------------------------
def element_visible(selector: str):
    def check(page) -> bool:
        loc = page.locator(selector)
        return loc.count() > 0 and loc.first.is_visible()
    return check


def element_absent(selector: str):
    def check(page) -> bool:
        return page.locator(selector).count() == 0
    return check


def element_count_is(selector: str, n: int):
    def check(page) -> bool:
        return page.locator(selector).count() == n
    return check


def all_of(*checks):
    def check(page) -> bool:
        return all(c(page) for c in checks)
    return check


def cell_text_is(tbody: str, row: int, col: int, expected: str):
    def check(page) -> bool:
        cell = page.locator(f"{tbody} tr").nth(row).locator("td").nth(col)
        return cell.inner_text().strip() == expected
    return check


# -- the extended suite: 22 further tasks -------------------------------------
TASKS.extend([
    Task(
        name="checkout_full",
        fixture="checkout_full.html",
        description="Three-stage checkout: address fields, payment "
                    "fields with a method radio, review, place order.",
        steps=[
            Step("fill", Target("textbox", label="Full name"), "Ada Lovelace",
                 verify=field_value_is("#co-name", "Ada Lovelace")),
            Step("fill", Target("textbox", label="Street address"), "12 Analytical Way",
                 verify=field_value_is("#co-street", "12 Analytical Way")),
            Step("fill", Target("textbox", label="City"), "London",
                 verify=field_value_is("#co-city", "London")),
            Step("fill", Target("textbox", label="ZIP code"), "12345",
                 verify=field_value_is("#co-zip", "12345")),
            Step("click", Target("button", text="Continue to payment"),
                 verify=element_visible("#co-step2")),
            Step("fill", Target("textbox", label="Card number"), "4242 4242 4242 4242",
                 verify=field_value_is("#co-card", "4242 4242 4242 4242")),
            Step("fill", Target("textbox", label="Expiry"), "1228",
                 verify=field_value_is("#co-exp", "1228")),
            Step("fill", Target("textbox", label="CVC"), "314",
                 verify=field_value_is("#co-cvc", "314")),
            Step("check", Target("radio", label="Card"),
                 verify=is_checked("#pm-card")),
            Step("click", Target("button", text="Review order"),
                 verify=text_contains("#co-review", "Ada Lovelace")),
            Step("click", Target("button", text="Place order"),
                 verify=text_is("#co-done", "Order confirmed. Total: $129.00")),
        ],
    ),
    Task(
        name="validation_form",
        fixture="validation_form.html",
        description="Registration form that rejects a bad email and "
                    "mismatched passwords; each error must be read, "
                    "corrected, and resubmitted.",
        steps=[
            Step("fill", Target("textbox", label="Full name"), "Ada Lovelace",
                 verify=field_value_is("#reg-name", "Ada Lovelace")),
            Step("fill", Target("textbox", label="Email"), "ada.example",
                 verify=field_value_is("#reg-email", "ada.example")),
            Step("fill", Target("textbox", label="Age"), "30",
                 verify=field_value_is("#reg-age", "30")),
            Step("fill", Target("textbox", label="Password"), "secret1",
                 verify=field_value_is("#reg-pass", "secret1")),
            Step("fill", Target("textbox", label="Confirm password"), "secret2",
                 verify=field_value_is("#reg-confirm", "secret2")),
            Step("click", Target("button", text="Register"),
                 verify=text_contains("#reg-errors", "valid email address")),
            Step("fill", Target("textbox", label="Email"), "ada@example.com",
                 verify=field_value_is("#reg-email", "ada@example.com")),
            Step("click", Target("button", text="Register"),
                 verify=text_contains("#reg-errors", "Passwords do not match")),
            Step("fill", Target("textbox", label="Confirm password"), "secret1",
                 verify=field_value_is("#reg-confirm", "secret1")),
            Step("click", Target("button", text="Register"),
                 verify=text_is("#reg-done", "Registration complete for Ada Lovelace")),
        ],
    ),
    Task(
        name="paginated_table",
        fixture="paginated_table.html",
        description="Paginated employee table: department filter, "
                    "score sort, and page navigation interact.",
        steps=[
            Step("select", Target("combobox", label="Department"), "Ops",
                 verify=visible_rows("#emp tr", 4)),
            Step("click", Target("button", text="Score"),
                 verify=first_cell_is("#emp", "Lena")),
            Step("select", Target("combobox", label="Department"), "All",
                 verify=all_of(visible_rows("#emp tr", 4),
                               first_cell_is("#emp", "June"))),
            Step("click", Target("button", text="Next"),
                 verify=all_of(text_is("#page-info", "Page 2 of 3"),
                               visible_rows("#emp tr", 4))),
            Step("click", Target("button", text="Next"),
                 verify=all_of(text_is("#page-info", "Page 3 of 3"),
                               visible_rows("#emp tr", 4))),
        ],
    ),
    Task(
        name="dependent_settings",
        fixture="dependent_settings.html",
        description="Preference toggles reveal dependent fields that "
                    "must be set before saving.",
        steps=[
            Step("check", Target("checkbox", label="Email notifications"),
                 verify=element_visible("#email-prefs")),
            Step("select", Target("combobox", label="Frequency"), "Weekly",
                 verify=field_value_is("#freq", "Weekly")),
            Step("check", Target("checkbox", label="Two-factor authentication"),
                 verify=element_visible("#twofa-prefs")),
            Step("select", Target("combobox", label="Second factor"), "SMS",
                 verify=field_value_is("#factor", "SMS")),
            Step("fill", Target("textbox", label="Phone number"), "555-0100",
                 verify=field_value_is("#phone", "555-0100")),
            Step("click", Target("button", text="Save preferences"),
                 verify=text_is("#prefs-saved", "Preferences saved")),
        ],
    ),
    Task(
        name="stacked_modals",
        fixture="stacked_modals.html",
        description="A second modal stacks over the first; the confirm "
                    "control lives in the top modal.",
        steps=[
            Step("click", Target("button", text="Open dialog"),
                 verify=element_visible("#modal-a")),
            Step("click", Target("button", text="Continue"),
                 verify=element_visible("#modal-b")),
            Step("check", Target("checkbox", label="I understand the terms"),
                 verify=is_checked("#understand")),
            Step("click", Target("button", text="Confirm"),
                 verify=text_is("#dlg-status", "All dialogs completed")),
        ],
    ),
    Task(
        name="delayed_render",
        fixture="delayed_render.html",
        description="Search results render late; the Open button for "
                    "the next step only appears after a wait.",
        steps=[
            Step("fill", Target("textbox", label="Query"), "alp",
                 verify=field_value_is("#query", "alp")),
            Step("click", Target("button", text="Search"),
                 verify=element_count_is("#results .result", 2)),
            Step("click", Target("button", text="Open"),
                 verify=text_is("#detail", "Opened: Alpha report")),
        ],
    ),
    Task(
        name="date_picker",
        fixture="date_picker.html",
        description="Date-picker style control: open the calendar "
                    "grid and pick a day cell.",
        steps=[
            Step("click", Target("textbox", label="Appointment day"),
                 verify=element_visible("#cal")),
            Step("click", Target("button", text="15"),
                 verify=field_value_is("#day-input", "Day 15")),
        ],
    ),
    Task(
        name="autocomplete_select",
        fixture="autocomplete_select.html",
        description="Search-and-select autocomplete: typing renders "
                    "suggestions; one must be picked to complete.",
        steps=[
            Step("fill", Target("textbox", label="Destination"), "alp",
                 verify=element_count_is("#suggestions button", 2)),
            Step("click", Target("button", text="Alpine Meadows"),
                 verify=text_is("#chosen", "Selected: Alpine Meadows")),
        ],
    ),
    Task(
        name="wizard_backtrack",
        fixture="wizard_backtrack.html",
        description="Wizard with a back step: go forward, return, "
                    "confirm values survived, then finish.",
        steps=[
            Step("fill", Target("textbox", label="First name"), "Ada",
                 verify=field_value_is("#wz-fname", "Ada")),
            Step("click", Target("button", text="Next"),
                 verify=element_visible("#wz-step2")),
            Step("fill", Target("textbox", label="Team name"), "Compilers",
                 verify=field_value_is("#wz-team", "Compilers")),
            Step("click", Target("button", text="Back"),
                 verify=all_of(element_visible("#wz-step1"),
                               field_value_is("#wz-fname", "Ada"))),
            Step("click", Target("button", text="Next"),
                 verify=all_of(element_visible("#wz-step2"),
                               field_value_is("#wz-team", "Compilers"))),
            Step("click", Target("button", text="Next"),
                 verify=text_contains("#wz-review", "Compilers")),
            Step("click", Target("button", text="Finish"),
                 verify=text_is("#wz-done", "Wizard complete for Ada")),
        ],
    ),
    Task(
        name="dependent_dropdowns",
        fixture="dependent_dropdowns.html",
        description="Country → state → city dropdowns where each "
                    "level's options depend on the previous choice.",
        steps=[
            Step("select", Target("combobox", label="Country"), "USA",
                 verify=field_value_is("#dd-country", "USA")),
            Step("select", Target("combobox", label="State"), "California",
                 verify=field_value_is("#dd-state", "California")),
            Step("select", Target("combobox", label="City"), "San Diego",
                 verify=text_is("#dd-summary", "Route: USA / California / San Diego")),
        ],
    ),
    Task(
        name="cart_update",
        fixture="cart_update.html",
        description="Cart: change a quantity (totals recalculate), "
                    "then remove the row entirely.",
        steps=[
            Step("fill", Target("textbox", name="qty-notebook"), "3",
                 verify=all_of(text_is("#line-notebook", "$12"),
                               text_is("#grand", "Total: $14"))),
            Step("click", Target("button", text="Remove"),
                 verify=visible_rows("#cart tr", 1)),
            Step("fill", Target("textbox", name="qty-pen"), "2",
                 verify=text_is("#grand", "Total: $4")),
        ],
    ),
    Task(
        name="tabbed_panels",
        fixture="tabbed_panels.html",
        description="Tabbed settings: work is spread across Profile, "
                    "Billing, and Security tabs.",
        steps=[
            Step("fill", Target("textbox", label="Display name"), "Ada",
                 verify=field_value_is("#disp-name", "Ada")),
            Step("click", Target("button", text="Billing"),
                 verify=element_visible("#panel-billing")),
            Step("select", Target("combobox", label="Plan cycle"), "Yearly",
                 verify=field_value_is("#plan-cycle", "Yearly")),
            Step("click", Target("button", text="Security"),
                 verify=element_visible("#panel-security")),
            Step("check", Target("checkbox", label="Login alerts"),
                 verify=is_checked("#login-alerts")),
            Step("click", Target("button", text="Save all"),
                 verify=text_is("#tabs-saved", "All settings saved")),
        ],
    ),
    Task(
        name="accordion_form",
        fixture="accordion_form.html",
        description="Accordion form: opening one section closes the "
                    "others; fill each while it is expanded.",
        steps=[
            Step("click", Target("button", text="Shipping details"),
                 verify=element_visible("#acc-ship")),
            Step("fill", Target("textbox", label="Street"), "1 Main St",
                 verify=field_value_is("#acc-street", "1 Main St")),
            Step("click", Target("button", text="Payment details"),
                 verify=element_visible("#acc-pay")),
            Step("fill", Target("textbox", label="Card number"), "4242",
                 verify=field_value_is("#acc-card", "4242")),
            Step("click", Target("button", text="Review notes"),
                 verify=element_visible("#acc-notes")),
            Step("fill", Target("textbox", label="Notes"), "Leave at door",
                 verify=field_value_is("#acc-note", "Leave at door")),
            Step("click", Target("button", text="Submit form"),
                 verify=text_is("#acc-done", "Form submitted")),
        ],
    ),
    Task(
        name="inline_edit_table",
        fixture="inline_edit_table.html",
        description="Inline row editing: Edit swaps cells for inputs "
                    "and itself for a Save button.",
        steps=[
            Step("click", Target("button", text="Edit"),
                 verify=element_count_is('input[name="edit-email"]', 1)),
            Step("fill", Target("textbox", name="edit-email"), "ada@new.example",
                 verify=field_value_is('input[name="edit-email"]', "ada@new.example")),
            Step("click", Target("button", text="Save row"),
                 verify=cell_text_is("#contacts", 0, 1, "ada@new.example")),
        ],
    ),
    Task(
        name="otp_code_entry",
        fixture="otp_code_entry.html",
        description="Segmented 4-digit code entry with auto-advancing "
                    "focus between boxes.",
        steps=[
            Step("fill", Target("textbox", label="Digit 1"), "4",
                 verify=field_value_is("#d1", "4")),
            Step("fill", Target("textbox", label="Digit 2"), "2",
                 verify=field_value_is("#d2", "2")),
            Step("fill", Target("textbox", label="Digit 3"), "0",
                 verify=field_value_is("#d3", "0")),
            Step("fill", Target("textbox", label="Digit 4"), "8",
                 verify=field_value_is("#d4", "8")),
            Step("click", Target("button", text="Verify code"),
                 verify=text_is("#otp-status", "Code verified")),
        ],
    ),
    Task(
        name="adversarial_double_label_change",
        fixture="adversarial_double_label.html",
        adversarial=True,
        description="The form's call-to-action is renamed twice "
                    "mid-task: 'Continue' → 'Proceed to address' → "
                    "'Place order', once per field typed into.",
        steps=[
            Step("fill", Target("textbox", label="Full name"), "Ada Lovelace",
                 verify=field_value_is("#ord-name", "Ada Lovelace")),
            Step("click",
                 Target("button", text="Continue", form="order-form", kind="submit"),
                 verify=element_visible("#panel2")),
            Step("fill", Target("textbox", label="Coupon code"), "SAVE10",
                 verify=field_value_is("#ord-coupon", "SAVE10")),
            Step("click",
                 Target("button", text="Proceed to address",
                        form="order-form", kind="submit"),
                 verify=text_is("#ord-success", "Order placed")),
        ],
    ),
    Task(
        name="adversarial_moved_button",
        fixture="adversarial_moved_button.html",
        adversarial=True,
        description="Checking gift wrap re-renders the action bar: "
                    "the working Checkout button moves into the order "
                    "summary and the toolbar keeps a stale same-label "
                    "button that only shows a hint.",
        steps=[
            Step("check", Target("checkbox", label="Add gift wrap"),
                 verify=is_checked("#giftwrap")),
            Step("click",
                 Target("button", text="Checkout",
                        form="order-summary", kind="submit"),
                 verify=text_is("#move-success", "Order confirmed")),
        ],
    ),
    Task(
        name="adversarial_banner_reappears",
        fixture="adversarial_banner.html",
        adversarial=True,
        description="A promo banner covering the lower viewport is "
                    "dismissed, but typing the coupon brings it back "
                    "over the Save button far down the page.",
        steps=[
            Step("click", Target("button", text="×"),
                 verify=element_absent("#banner")),
            Step("fill", Target("textbox", label="Coupon code"), "SAVE10",
                 verify=field_value_is("#coupon", "SAVE10")),
            Step("click",
                 Target("button", text="Save changes",
                        form="panel2", kind="submit"),
                 verify=text_is("#saved-msg", "Changes saved")),
        ],
    ),
    Task(
        name="adversarial_late_overlay",
        fixture="adversarial_late_overlay.html",
        adversarial=True,
        description="The Confirm button never moves or changes; a "
                    "full-screen promo overlay raised by the previous "
                    "click covers it and intercepts the click.",
        steps=[
            Step("click", Target("button", text="Proceed to confirmation"),
                 verify=element_visible("#confirm-panel")),
            Step("click",
                 Target("button", text="Confirm order",
                        form="confirm-panel", kind="submit"),
                 verify=text_is("#late-done", "Order confirmed")),
        ],
    ),
    Task(
        name="adversarial_renamed_field",
        fixture="adversarial_renamed_field.html",
        adversarial=True,
        description="Choosing Canada renames the postal field's "
                    "label from 'ZIP code' to 'Postal code'; the "
                    "field itself never moves.",
        steps=[
            Step("select", Target("combobox", label="Country"), "Canada",
                 verify=field_value_is("#country", "Canada")),
            Step("fill",
                 Target("textbox", label="ZIP code", form="postal-form"), "K1A 0B1",
                 verify=field_value_is("#postal", "K1A 0B1")),
            Step("click", Target("button", text="Save address"),
                 verify=text_is("#addr-saved", "Address saved")),
        ],
    ),
    Task(
        name="adversarial_decoy_button",
        fixture="adversarial_decoy.html",
        adversarial=True,
        description="Opting into partner offers inserts a same-label "
                    "'Subscribe' decoy above the real form; it only "
                    "reports that the offer has ended.",
        steps=[
            Step("fill", Target("textbox", label="Email address"), "ada@example.com",
                 verify=field_value_is("#nl-email", "ada@example.com")),
            Step("check", Target("checkbox", label="Email me partner offers too"),
                 verify=is_checked("#partner")),
            Step("click",
                 Target("button", text="Subscribe",
                        form="newsletter-form", kind="submit"),
                 verify=text_is("#nl-done", "Subscribed ada@example.com")),
        ],
    ),
    Task(
        name="adversarial_rename_under_overlay",
        fixture="adversarial_rename_overlay.html",
        adversarial=True,
        description="Typing the card number renames the pay button "
                    "and raises a cookie bar over it at the same "
                    "time; recovery must re-ground and dismiss.",
        steps=[
            Step("fill", Target("textbox", label="Name on card"), "Ada Lovelace",
                 verify=field_value_is("#cc-name", "Ada Lovelace")),
            Step("fill", Target("textbox", label="Card number"), "4242",
                 verify=field_value_is("#cc-num", "4242")),
            Step("click",
                 Target("button", text="Pay now", form="pay-form", kind="submit"),
                 verify=text_is("#pay-success", "Payment confirmed")),
        ],
    ),
])


# -- business-workflow suite: 3 further tasks --------------------------------
TASKS.extend([
    Task(
        name="crm_record_update",
        fixture="crm_customers.html",
        description="CRM: search the customer table down to one "
                    "record, open it for editing, change its status, "
                    "phone and notes, save, and confirm the table "
                    "shows the saved values.",
        steps=[
            Step("fill", Target("textbox", label="Search"), "Pulseworks",
                 verify=visible_rows("#customers tr", 1)),
            Step("click", Target("button", text="Edit"),
                 verify=element_visible("#crm-edit")),
            Step("select", Target("combobox", label="Status"), "Active",
                 verify=field_value_is("#crm-status", "Active")),
            Step("fill", Target("textbox", label="Phone"), "555-0142",
                 verify=field_value_is("#crm-phone", "555-0142")),
            Step("fill", Target("textbox", label="Notes"),
                 "Renewal confirmed for November",
                 verify=field_value_is("#crm-note",
                                       "Renewal confirmed for November")),
            Step("click", Target("button", text="Save changes"),
                 verify=all_of(
                     text_is("#crm-saved", "Record saved for Pulseworks"),
                     cell_text_is("#customers", 0, 2, "Active"),
                     cell_text_is("#customers", 0, 3, "555-0142"))),
        ],
    ),
    Task(
        name="vendor_application",
        fixture="vendor_application.html",
        description="Four-step vendor application (company, contact, "
                    "details, review, submit). The contact step "
                    "rejects a malformed email mid-flow; it must be "
                    "corrected before the application can proceed.",
        steps=[
            Step("fill", Target("textbox", label="Company name"),
                 "Northbeam Traders",
                 verify=field_value_is("#va-company", "Northbeam Traders")),
            Step("select", Target("combobox", label="Industry"), "Software",
                 verify=field_value_is("#va-industry", "Software")),
            Step("click", Target("button", text="Next"),
                 verify=element_visible("#va-step2")),
            Step("fill", Target("textbox", label="Contact name"), "Marta Chen",
                 verify=field_value_is("#va-contact", "Marta Chen")),
            Step("fill", Target("textbox", label="Email"), "marta@northbeam",
                 verify=field_value_is("#va-email", "marta@northbeam")),
            Step("fill", Target("textbox", label="Phone"), "555-0117",
                 verify=field_value_is("#va-phone", "555-0117")),
            Step("click", Target("button", text="Next"),
                 verify=text_contains("#va-errors", "valid email address")),
            Step("fill", Target("textbox", label="Email"),
                 "marta@northbeam.example",
                 verify=field_value_is("#va-email", "marta@northbeam.example")),
            Step("click", Target("button", text="Next"),
                 verify=element_visible("#va-step3")),
            Step("select", Target("combobox", label="Category"), "Software",
                 verify=field_value_is("#va-category", "Software")),
            Step("fill", Target("textbox", label="Expected monthly orders"),
                 "250",
                 verify=field_value_is("#va-orders", "250")),
            Step("check", Target("checkbox", label="ISO 9001 certified"),
                 verify=is_checked("#va-iso")),
            Step("click", Target("button", text="Next"),
                 verify=text_contains("#va-review", "Northbeam Traders")),
            Step("click", Target("button", text="Submit application"),
                 verify=text_is("#va-done",
                                "Vendor application submitted for "
                                "Northbeam Traders")),
        ],
    ),
    Task(
        name="lead_entry",
        fixture="lead_entry.html",
        description="Enter each lead from the inbox panel into the "
                    "entered-leads table. The third inbox item repeats "
                    "the first lead's email: the form refuses it with "
                    "a duplicate warning and no new row is added.",
        steps=[
            Step("fill", Target("textbox", label="Full name"), "Ravi Shah",
                 verify=field_value_is("#lead-name", "Ravi Shah")),
            Step("fill", Target("textbox", label="Email"),
                 "ravi@brightpath.example",
                 verify=field_value_is("#lead-email", "ravi@brightpath.example")),
            Step("fill", Target("textbox", label="Company"), "Brightpath",
                 verify=field_value_is("#lead-company", "Brightpath")),
            Step("click", Target("button", text="Add lead"),
                 verify=all_of(visible_rows("#entered tr", 1),
                               cell_text_is("#entered", 0, 0, "Ravi Shah"))),
            Step("fill", Target("textbox", label="Full name"), "Elena Brooks",
                 verify=field_value_is("#lead-name", "Elena Brooks")),
            Step("fill", Target("textbox", label="Email"),
                 "elena@harborline.example",
                 verify=field_value_is("#lead-email",
                                       "elena@harborline.example")),
            Step("fill", Target("textbox", label="Company"), "Harborline",
                 verify=field_value_is("#lead-company", "Harborline")),
            Step("click", Target("button", text="Add lead"),
                 verify=visible_rows("#entered tr", 2)),
            Step("fill", Target("textbox", label="Full name"), "Ravi Shah",
                 verify=field_value_is("#lead-name", "Ravi Shah")),
            Step("fill", Target("textbox", label="Email"),
                 "ravi@brightpath.example",
                 verify=field_value_is("#lead-email", "ravi@brightpath.example")),
            Step("fill", Target("textbox", label="Company"), "Brightpath",
                 verify=field_value_is("#lead-company", "Brightpath")),
            Step("click", Target("button", text="Add lead"),
                 verify=all_of(
                     text_contains("#lead-warning", "already exists"),
                     visible_rows("#entered tr", 2))),
            Step("fill", Target("textbox", label="Full name"), "Tom Okafor",
                 verify=field_value_is("#lead-name", "Tom Okafor")),
            Step("fill", Target("textbox", label="Email"),
                 "tom@okafor.example",
                 verify=field_value_is("#lead-email", "tom@okafor.example")),
            Step("fill", Target("textbox", label="Company"),
                 "Okafor Consulting",
                 verify=field_value_is("#lead-company", "Okafor Consulting")),
            Step("click", Target("button", text="Add lead"),
                 verify=all_of(visible_rows("#entered tr", 3),
                               cell_text_is("#entered", 2, 0, "Tom Okafor"),
                               cell_text_is("#entered", 2, 1,
                                            "tom@okafor.example"))),
        ],
    ),
])


# Category of each task, used for the per-category breakdown in RESULTS.md.
TASK_CATEGORIES: dict[str, str] = {
    "login": "Forms & wizards",
    "multistep_form": "Forms & wizards",
    "settings_form": "Forms & wizards",
    "checkout_full": "Forms & wizards",
    "validation_form": "Forms & wizards",
    "dependent_settings": "Forms & wizards",
    "wizard_backtrack": "Forms & wizards",
    "dependent_dropdowns": "Forms & wizards",
    "accordion_form": "Forms & wizards",
    "otp_code_entry": "Forms & wizards",
    "table_filter": "Tables, lists & cart",
    "todo_list": "Tables, lists & cart",
    "sort_table": "Tables, lists & cart",
    "paginated_table": "Tables, lists & cart",
    "cart_update": "Tables, lists & cart",
    "inline_edit_table": "Tables, lists & cart",
    "stacked_modals": "Widgets & dialogs",
    "delayed_render": "Widgets & dialogs",
    "date_picker": "Widgets & dialogs",
    "autocomplete_select": "Widgets & dialogs",
    "tabbed_panels": "Widgets & dialogs",
    "adversarial_label_change": "Adversarial recovery",
    "adversarial_overlay_move": "Adversarial recovery",
    "adversarial_double_label_change": "Adversarial recovery",
    "adversarial_moved_button": "Adversarial recovery",
    "adversarial_banner_reappears": "Adversarial recovery",
    "adversarial_late_overlay": "Adversarial recovery",
    "adversarial_renamed_field": "Adversarial recovery",
    "adversarial_decoy_button": "Adversarial recovery",
    "adversarial_rename_under_overlay": "Adversarial recovery",
    "crm_record_update": "Business workflows",
    "vendor_application": "Business workflows",
    "lead_entry": "Business workflows",
}
