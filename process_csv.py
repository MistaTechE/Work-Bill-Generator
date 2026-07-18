#process_csv

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
