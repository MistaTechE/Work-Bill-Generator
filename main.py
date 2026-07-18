#main.py
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
