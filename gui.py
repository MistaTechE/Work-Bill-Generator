#gui.py
# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from process_csv import process_csv

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
