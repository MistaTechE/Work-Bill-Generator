#main.py

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
