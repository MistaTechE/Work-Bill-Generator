#pdf_fill.py
# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------
from config import today_mmddyyyy, format_money,
from pypdf import PdfReader, PdfWriter
from datetime import date

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
