"""Page observation: snapshot the interactive elements of a page.

Each element record carries a stable ref (e1, e2, ...) within one snapshot
plus the semantic attributes (tag, role, text, id, name, label, form) the
agent uses to ground a task target, and a locator recipe to act on it.
"""
from __future__ import annotations

SNAPSHOT_JS = r"""
() => {
  const sel = 'a, button, input, select, textarea, [role="button"], [role="link"]';
  const out = [];
  document.querySelectorAll(sel).forEach((el) => {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    const visible = r.width > 0 && r.height > 0 &&
                    st.visibility !== 'hidden' && st.display !== 'none';
    let label = '';
    if (el.id) {
      const lab = document.querySelector('label[for="' + el.id + '"]');
      if (lab) label = lab.innerText.trim();
    }
    if (!label && el.closest('label')) label = el.closest('label').innerText.trim();
    out.push({
      tag: el.tagName.toLowerCase(),
      type: (el.getAttribute('type') || '').toLowerCase(),
      role: el.getAttribute('role') || '',
      id: el.id || '',
      name: el.getAttribute('name') || '',
      text: (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 80),
      value: (el.value || ''),
      placeholder: el.getAttribute('placeholder') || '',
      aria: el.getAttribute('aria-label') || '',
      label: label,
      form: el.form ? (el.form.id || '') : '',
      ancestors: (() => {
        const ids = [];
        let n = el.parentElement;
        while (n && ids.length < 6) {
          if (n.id) ids.push(n.id);
          n = n.parentElement;
        }
        return ids;
      })(),
      visible: visible,
      disabled: !!el.disabled,
    });
  });
  return out;
}
"""


def locator_recipe(rec: dict) -> str | None:
    """Build a Playwright CSS/text locator for a snapshot record."""
    if rec["id"]:
        return f"#{rec['id']}"
    if rec["name"]:
        return f"{rec['tag']}[name=\"{rec['name']}\"]"
    text = rec["text"] or rec["aria"]
    if text and rec["tag"] in ("button", "a"):
        return f"{rec['tag']}:has-text(\"{text}\")"
    if rec["placeholder"]:
        return f"[placeholder=\"{rec['placeholder']}\"]"
    return None


class Snapshot:
    def __init__(self, records: list[dict]):
        self.elements: list[dict] = []
        for i, rec in enumerate(records, start=1):
            rec = dict(rec)
            rec["ref"] = f"e{i}"
            rec["recipe"] = locator_recipe(rec)
            self.elements.append(rec)

    @classmethod
    def take(cls, page) -> "Snapshot":
        return cls(page.evaluate(SNAPSHOT_JS))

    def __len__(self) -> int:
        return len(self.elements)
