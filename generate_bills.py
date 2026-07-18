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

