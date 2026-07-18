#python generate_bills.py
"""
Work Bill Generator
--------------------
Reads a CSV of device-repair/non-return charges and creates a bill with a PDF, saving
each finished bill into a "bills" folder on the Desktop.
It also auto-assigns Invoice # for any row that doesn't already have
one, using the school-year format (25-101 for
the 2025-26 school year, 26-101 for the 2026-27 school year etc), and writes those new numbers back into the
CSV so numbers are never reused.
"""
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


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

def build_bill_pdf(row: dict, output_path: Path):
    bill_date = row.get(COL_BILL_CREATED, "").strip() or today_mmddyyyy()
    last = row.get(COL_LAST, "").strip()
    first = row.get(COL_FIRST, "").strip()
    charge = format_money(row.get(COL_CHARGE, ""))

    fields = {
        "Date": bill_date,
        "ToName": f"Parents of {last} {first}".strip(),
        "OrderNo": row.get(COL_INVOICE, "").strip(),
        "POAddr": row.get(COL_ADDRESS, "").strip(),
        "Date1": bill_date,
        "Desc1": row.get(COL_NOTES, "").strip(),
        # Clear the chromebook-repair-specific boilerplate rows from the
        # original template; keep rows 8-11 & 15-17 (payment instructions,
        # school address, phone number, ORG/PROGRAM/OBJ codes) as-is.
        "Desc2": "",
        "Desc3": "",
        "Desc4": "",
        "Desc5": "",
        "Desc6": "",
        "Desc7": "",
        "Price1": charge,
        "Ext1": charge,
        "Total18": charge,
    }

    reader = PdfReader(str(TEMPLATE_PATH))
    writer = PdfWriter()
    writer.append(reader)
    writer.update_page_form_field_values(writer.pages[0], fields)
    try:
        writer.set_need_appearances_writer(True)
    except Exception:
        pass

    with open(output_path, "wb") as f:
        writer.write(f)


# ---------------------------------------------------------------------------
# Main processing routine (shared by GUI and CLI)
# ---------------------------------------------------------------------------

def process_csv(csv_path: Path, log=print):
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template PDF not found at {TEMPLATE_PATH}")

    fieldnames, rows = read_csv_rows(csv_path)
    validate_columns(fieldnames)

    if not rows:
        log("The CSV has no data rows — nothing to generate.")
        return

    assigned = assign_missing_invoice_numbers(rows)
    if assigned:
        write_csv_rows(csv_path, fieldnames, rows)
        log("Assigned new invoice numbers for blank rows and saved them back to the CSV.")

    desktop = Path.home() / "Desktop"
    bills_folder = desktop / "bills"
    bills_folder.mkdir(parents=True, exist_ok=True)

    count = 0
    for row in rows:
        last = sanitize_filename(row.get(COL_LAST, "").strip() or "Unknown")
        first = sanitize_filename(row.get(COL_FIRST, "").strip() or "Unknown")
        invoice = sanitize_filename(row.get(COL_INVOICE, "").strip() or "NoInvoice")
        filename = f"{invoice}_{last}_{first}.pdf"
        output_path = bills_folder / filename

        try:
            build_bill_pdf(row, output_path)
            count += 1
            log(f"Created: {filename}")
        except Exception as e:
            log(f"FAILED on invoice {invoice} ({first} {last}): {e}")

    log(f"\nDone. {count} bill(s) saved to: {bills_folder}")
    return bills_folder, count


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext


class BillGeneratorApp:
    def __init__(self, root):
        self.root = root
        root.title("Work Bill Generator")
        root.geometry("560x420")
        root.resizable(False, False)

        tk.Label(
            root, text="Work Bill Generator", font=("Segoe UI", 16, "bold")
        ).pack(pady=(16, 4))
        tk.Label(
            root,
            text="Select your billing CSV to generate bills into\n"
                 "a 'bills' folder on your Desktop.",
            font=("Segoe UI", 10),
            justify="center",
        ).pack(pady=(0, 12))

        tk.Button(
            root,
            text="Select CSV and Generate Bills",
            font=("Segoe UI", 11),
            command=self.select_and_run,
            padx=12,
            pady=8,
        ).pack(pady=8)

        self.log_box = scrolledtext.ScrolledText(
            root, width=68, height=16, font=("Consolas", 9)
        )
        self.log_box.pack(padx=12, pady=12)
        self.log_box.configure(state="disabled")

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state="disabled")
        self.root.update_idletasks()

    def select_and_run(self):
        csv_path = filedialog.askopenfilename(
            title="Select billing CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not csv_path:
            return

        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", tk.END)
        self.log_box.configure(state="disabled")

        self.log(f"Processing: {csv_path}\n")
        try:
            result = process_csv(Path(csv_path), log=self.log)
            if result:
                bills_folder, count = result
                messagebox.showinfo(
                    "Done",
                    f"{count} bill(s) generated.\nSaved to: {bills_folder}",
                )
        except Exception as e:
            self.log(f"\nERROR: {e}")
            messagebox.showerror("Error", str(e))


def main():
    # Optional CLI mode: python generate_bills.py path/to/file.csv
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
        if not csv_path.exists():
            print(f"File not found: {csv_path}")
            sys.exit(1)
        process_csv(csv_path)
        return

    root = tk.Tk()
    BillGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
