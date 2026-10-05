"""
gui.py - Modern graphical user interface for TES3Localizer with engine info and selection.
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

from core.extractor import run_extraction
from core.translator import run_translation
from core.builder import run_build

class TES3LocalizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TES3Localizer - Morrowind & OpenMW Localization Tool")
        self.root.geometry("680x560")
        self.root.resizable(False, False)

        style = ttk.Style()
        style.theme_use("clam")

        # Header Frame
        header = ttk.Frame(root, padding="15")
        header.pack(fill=tk.X)
        title_lbl = ttk.Label(header, text="TES3Localizer", font=("Segoe UI", 16, "bold"))
        title_lbl.pack(anchor="w")
        desc_lbl = ttk.Label(header, text="Lossless, topic-preserving dialogue translation toolchain for TES3 / OpenMW", font=("Segoe UI", 9))
        desc_lbl.pack(anchor="w")

        # Main Notebook
        self.notebook = ttk.Notebook(root, padding="10")
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Build ESP
        self.tab_build = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_build, text="Build ESP Patch")
        self.setup_build_tab()

        # Tab 2: Extract Dialogues
        self.tab_extract = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_extract, text="Extract to JSON")
        self.setup_extract_tab()

        # Tab 3: Translate
        self.tab_translate = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_translate, text="Translate JSON")
        self.setup_translate_tab()

        # Status Bar
        self.status_var = tk.StringVar(value="Ready.")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w", padding="6")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_build_tab(self):
        ttk.Label(self.tab_build, text="Master File (.esm):").pack(anchor="w", pady=(5, 2))
        f1 = ttk.Frame(self.tab_build)
        f1.pack(fill=tk.X, pady=(0, 10))
        self.build_esm_var = tk.StringVar()
        ttk.Entry(f1, textvariable=self.build_esm_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(f1, text="Browse...", command=lambda: self.browse_file(self.build_esm_var, [("ESM files", "*.esm"), ("All files", "*.*")])).pack(side=tk.RIGHT)

        ttk.Label(self.tab_build, text="Translated Dialogue JSON:").pack(anchor="w", pady=(5, 2))
        f2 = ttk.Frame(self.tab_build)
        f2.pack(fill=tk.X, pady=(0, 10))
        self.build_json_var = tk.StringVar()
        ttk.Entry(f2, textvariable=self.build_json_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(f2, text="Browse...", command=lambda: self.browse_file(self.build_json_var, [("JSON files", "*.json")])).pack(side=tk.RIGHT)

        ttk.Label(self.tab_build, text="Output Patch (.esp):").pack(anchor="w", pady=(5, 2))
        f3 = ttk.Frame(self.tab_build)
        f3.pack(fill=tk.X, pady=(0, 15))
        self.build_out_var = tk.StringVar(value="Polonizacja_PL.esp")
        ttk.Entry(f3, textvariable=self.build_out_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(f3, text="Browse...", command=lambda: self.browse_save_file(self.build_out_var, [("ESP files", "*.esp")])).pack(side=tk.RIGHT)

        btn = ttk.Button(self.tab_build, text="Build ESP Plugin", command=self.do_build)
        btn.pack(pady=10, fill=tk.X)

    def setup_extract_tab(self):
        ttk.Label(self.tab_extract, text="Master Files to Scan (e.g. Morrowind.esm, TR_Mainland.esm):").pack(anchor="w", pady=(5, 2))
        f1 = ttk.Frame(self.tab_extract)
        f1.pack(fill=tk.X, pady=(0, 10))
        self.extract_esm_var = tk.StringVar()
        ttk.Entry(f1, textvariable=self.extract_esm_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(f1, text="Browse...", command=lambda: self.browse_file(self.extract_esm_var, [("ESM files", "*.esm")])).pack(side=tk.RIGHT)

        ttk.Label(self.tab_extract, text="Output Dialogues JSON:").pack(anchor="w", pady=(5, 2))
        f2 = ttk.Frame(self.tab_extract)
        f2.pack(fill=tk.X, pady=(0, 10))
        self.extract_json_var = tk.StringVar(value="extracted_dialogues.json")
        ttk.Entry(f2, textvariable=self.extract_json_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(f2, text="Browse...", command=lambda: self.browse_save_file(self.extract_json_var, [("JSON files", "*.json")])).pack(side=tk.RIGHT)

        ttk.Label(self.tab_extract, text="Output Topics/Keywords List (TXT):").pack(anchor="w", pady=(5, 2))
        f3 = ttk.Frame(self.tab_extract)
        f3.pack(fill=tk.X, pady=(0, 15))
        self.extract_top_var = tk.StringVar(value="preserved_topics.txt")
        ttk.Entry(f3, textvariable=self.extract_top_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(f3, text="Browse...", command=lambda: self.browse_save_file(self.extract_top_var, [("TXT files", "*.txt")])).pack(side=tk.RIGHT)

        btn = ttk.Button(self.tab_extract, text="Extract Dialogues & Topics", command=self.do_extract)
        btn.pack(pady=10, fill=tk.X)

    def setup_translate_tab(self):
        # Engine Selection & Info
        eng_frame = ttk.LabelFrame(self.tab_translate, text="Translation Engine & Service", padding="8")
        eng_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(eng_frame, text="Active Engine:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.engine_var = tk.StringVar(value="Google Translate (Free / Default)")
        engine_combo = ttk.Combobox(eng_frame, textvariable=self.engine_var, values=["Google Translate (Free / Default)", "DeepL API (Requires Key)"], state="readonly")
        engine_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        eng_frame.columnconfigure(1, weight=1)

        self.engine_desc_lbl = ttk.Label(eng_frame, text="Engine Info: Free automated translation using Google Translate. Preserves all {P0} topic tokens.", font=("Segoe UI", 8, "italic"), foreground="gray")
        self.engine_desc_lbl.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=(2, 0))

        # Input JSON
        ttk.Label(self.tab_translate, text="Input Dialogues JSON:").pack(anchor="w", pady=(5, 2))
        f1 = ttk.Frame(self.tab_translate)
        f1.pack(fill=tk.X, pady=(0, 8))
        self.trans_in_var = tk.StringVar(value="extracted_dialogues.json")
        ttk.Entry(f1, textvariable=self.trans_in_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(f1, text="Browse...", command=lambda: self.browse_file(self.trans_in_var, [("JSON files", "*.json")])).pack(side=tk.RIGHT)

        # Preserved Topics
        ttk.Label(self.tab_translate, text="Preserved Topics / Keywords List (TXT):").pack(anchor="w", pady=(5, 2))
        f2 = ttk.Frame(self.tab_translate)
        f2.pack(fill=tk.X, pady=(0, 8))
        self.trans_top_var = tk.StringVar(value="preserved_topics.txt")
        ttk.Entry(f2, textvariable=self.trans_top_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(f2, text="Browse...", command=lambda: self.browse_file(self.trans_top_var, [("TXT files", "*.txt")])).pack(side=tk.RIGHT)

        # Language
        ttk.Label(self.tab_translate, text="Target Language Code (e.g. pl, de, es, fr, it, cs, uk):").pack(anchor="w", pady=(5, 2))
        self.trans_lang_var = tk.StringVar(value="pl")
        ttk.Entry(self.tab_translate, textvariable=self.trans_lang_var).pack(fill=tk.X, pady=(0, 12))

        btn = ttk.Button(self.tab_translate, text="Start Translation", command=self.do_translate)
        btn.pack(pady=5, fill=tk.X)

    def browse_file(self, target_var, filetypes):
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            target_var.set(path)

    def browse_save_file(self, target_var, filetypes):
        path = filedialog.asksaveasfilename(filetypes=filetypes)
        if path:
            target_var.set(path)

    def do_build(self):
        esm = self.build_esm_var.get()
        j = self.build_json_var.get()
        out = self.build_out_var.get()
        if not esm or not j or not out:
            messagebox.showerror("Error", "Please fill in all paths.")
            return

        def run():
            self.status_var.set("Building ESP patch in background...")
            try:
                run_build(esm, j, out)
                self.status_var.set(f"Done! ESP created: {out}")
                messagebox.showinfo("Success", f"ESP plugin created successfully!\nPath: {out}")
            except Exception as e:
                self.status_var.set(f"Error: {e}")
                messagebox.showerror("Error", str(e))

        threading.Thread(target=run, daemon=True).start()

    def do_extract(self):
        esm = self.extract_esm_var.get()
        j = self.extract_json_var.get()
        top = self.extract_top_var.get()
        if not esm or not j:
            messagebox.showerror("Error", "Please specify ESM file.")
            return

        def run():
            self.status_var.set("Extracting records from ESM...")
            try:
                run_extraction([esm], j, top)
                self.status_var.set(f"Extraction complete! Saved to {j}")
                messagebox.showinfo("Success", f"Dialogues and topics extracted successfully!\nSaved to: {j}")
            except Exception as e:
                self.status_var.set(f"Error: {e}")
                messagebox.showerror("Error", str(e))

        threading.Thread(target=run, daemon=True).start()

    def do_translate(self):
        inp = self.trans_in_var.get()
        top = self.trans_top_var.get()
        lang = self.trans_lang_var.get()
        engine_str = "deepl" if "deepl" in self.engine_var.get().lower() else "google"
        out = f"dialogues_{lang}.json"

        if not inp or not top:
            messagebox.showerror("Error", "Please specify JSON and topics file.")
            return

        def run():
            self.status_var.set(f"Translating using [{engine_str.upper()}] to '{lang}'...")
            try:
                run_translation(inp, out, top, target_lang=lang, engine=engine_str)
                self.status_var.set(f"Translation complete using [{engine_str.upper()}]! Saved to {out}")
                messagebox.showinfo("Success", f"Translation finished successfully!\nEngine: {engine_str.upper()}\nSaved to: {out}")
            except Exception as e:
                self.status_var.set(f"Error: {e}")
                messagebox.showerror("Error", str(e))

        threading.Thread(target=run, daemon=True).start()

def launch_gui():
    root = tk.Tk()
    app = TES3LocalizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
