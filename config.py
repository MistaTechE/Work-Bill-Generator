#config.py
import csv
import os
import re
import sys
from datetime import date
from pathlib import Path
from pypdf import PdfReader, PdfWriter

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR / "template" / "Form_99_Bill_Template.pdf"

# Columns expected in the CSV (must match your sheet's header row exactly)
COL_INVOICE = "Invoice #"
COL_STATE_TAG = "STATE TAG"
COL_LAST = "Student Last Name"
COL_FIRST = "Student First Name"
COL_GRADE = "Grade"
COL_NOTES = "Notes"
COL_CHARGE = "Charge Amount"
COL_ADDRESS = "Address"
COL_BILL_CREATED = "Bill Created"

REQUIRED_COLUMNS = [
    COL_INVOICE, COL_LAST, COL_FIRST, COL_NOTES, COL_CHARGE, COL_ADDRESS,
]

INVOICE_PATTERN = re.compile(r"^(\d{2})-(\d{3})$")


# ---------------------------------------------------------------------------
# Invoice number logic
# ---------------------------------------------------------------------------

def current_school_year_prefix(today: date = None) -> str:
    """
    Returns the 2-digit school-year prefix used in invoice numbers.
    School year runs Aug 1 - Jul 31. Aug 2025 - Jul 2026 => '25'.
    """
    today = today or date.today()
    year = today.year if today.month >= 8 else today.year - 1
    return f"{year % 100:02d}"


def next_invoice_number(existing_invoices, prefix: str) -> str:
    """
    Given all invoice numbers already in the sheet, find the highest
    sequence number used for this school-year prefix and return the
    next one, formatted like '25-101'.
    """
    highest = 0
    for inv in existing_invoices:
        match = INVOICE_PATTERN.match(inv.strip())
        if match and match.group(1) == prefix:
            highest = max(highest, int(match.group(2)))
    return f"{prefix}-{highest + 1:03d}"


def assign_missing_invoice_numbers(rows):
    """
    Fills in blank Invoice # cells in-place, using sequential numbers
    for the current school year. Returns True if any were assigned.
    """
    prefix = current_school_year_prefix()
    existing = [r[COL_INVOICE] for r in rows if r.get(COL_INVOICE, "").strip()]
    changed = False
    for row in rows:
        if not row.get(COL_INVOICE, "").strip():
            new_number = next_invoice_number(existing, prefix)
            row[COL_INVOICE] = new_number
            existing.append(new_number)
            changed = True
    return changed

def format_money(raw: str) -> str:
    """Turns '$350', '350', '350.5' etc. into '350.00' (no $ sign, since
    the PDF's own table columns already imply dollars)."""
    if not raw:
        return ""
    cleaned = raw.replace("$", "").replace(",", "").strip()
    try:
        return f"{float(cleaned):.2f}"
    except ValueError:
        return raw  # leave as-is if it isn't a plain number


def sanitize_filename(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text).strip()
    return re.sub(r"[\s]+", "_", text)


def today_mmddyyyy() -> str:
    return date.today().strftime("%m/%d/%Y")


def read_csv_rows(csv_path: Path):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = [dict(row) for row in reader]
    return fieldnames, rows


def write_csv_rows(csv_path: Path, fieldnames, rows):
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def validate_columns(fieldnames):
    missing = [c for c in REQUIRED_COLUMNS if c not in fieldnames]
    if missing:
        raise ValueError(
            "The CSV is missing these expected column(s): "
            + ", ".join(missing)
            + "\n\nExpected columns include: " + ", ".join(REQUIRED_COLUMNS)
        )
