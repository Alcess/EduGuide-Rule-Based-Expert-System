"""Tkinter interface for the EduGuide student advising prototype."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText


class MainView:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("EduGuide Student Advising System")
        self.root.geometry("1180x760")
        self.root.minsize(1020, 680)

        self.input_vars: dict[str, tk.StringVar] = {}
        self.comboboxes: dict[str, ttk.Combobox] = {}
        self.output_text: ScrolledText | None = None
        self.status_var = tk.StringVar(value="Load the dataset to begin.")

        self.load_dataset_button: ttk.Button | None = None
        self.evaluate_button: ttk.Button | None = None
        self.generate_report_button: ttk.Button | None = None
        self.save_report_button: ttk.Button | None = None
        self.open_report_button: ttk.Button | None = None
        self.verify_button: ttk.Button | None = None

        self._build_layout()

    def _build_layout(self) -> None:
        main_frame = ttk.Frame(self.root, padding=16)
        main_frame.pack(fill="both", expand=True)

        title_label = ttk.Label(
            main_frame,
            text="EduGuide Prototype: Rule-Based Student Advising System",
            font=("Segoe UI", 16, "bold"),
        )
        title_label.pack(anchor="w")

        notice_label = ttk.Label(
            main_frame,
            text="Educational demo only. Custom SHA-256 is used for report integrity and a demo-only XOR stream cipher.",
            font=("Segoe UI", 10),
        )
        notice_label.pack(anchor="w", pady=(4, 10))

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)
        content_frame.columnconfigure(0, weight=0)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)

        input_frame = ttk.LabelFrame(content_frame, text="Student Input", padding=14)
        input_frame.grid(row=0, column=0, sticky="nsw", padx=(0, 12))

        field_specs = [
            ("Attendance", "Attendance (%)", "entry"),
            ("Hours_Studied", "Hours Studied", "entry"),
            ("Previous_Scores", "Previous Scores", "entry"),
            ("Exam_Score", "Exam Score", "entry"),
            ("Tutoring_Sessions", "Tutoring Sessions", "entry"),
            ("Parental_Involvement", "Parental Involvement", "combo"),
            ("Access_to_Resources", "Access to Resources", "combo"),
            ("Internet_Access", "Internet Access", "combo"),
        ]

        for row_index, (field_name, label_text, field_type) in enumerate(field_specs):
            ttk.Label(input_frame, text=label_text).grid(row=row_index, column=0, sticky="w", pady=4)
            variable = tk.StringVar()
            self.input_vars[field_name] = variable

            if field_type == "combo":
                widget = ttk.Combobox(input_frame, textvariable=variable, state="readonly", width=20)
                widget.grid(row=row_index, column=1, sticky="ew", pady=4)
                self.comboboxes[field_name] = widget
            else:
                widget = ttk.Entry(input_frame, textvariable=variable, width=24)
                widget.grid(row=row_index, column=1, sticky="ew", pady=4)

        input_frame.columnconfigure(1, weight=1)

        button_frame = ttk.LabelFrame(input_frame, text="Actions", padding=10)
        button_frame.grid(row=len(field_specs), column=0, columnspan=2, sticky="ew", pady=(14, 0))
        button_frame.columnconfigure(0, weight=1)

        self.load_dataset_button = ttk.Button(button_frame, text="Load Dataset")
        self.load_dataset_button.grid(row=0, column=0, sticky="ew", pady=3)

        self.evaluate_button = ttk.Button(button_frame, text="Evaluate Student")
        self.evaluate_button.grid(row=1, column=0, sticky="ew", pady=3)

        self.generate_report_button = ttk.Button(button_frame, text="Generate Report")
        self.generate_report_button.grid(row=2, column=0, sticky="ew", pady=3)

        self.save_report_button = ttk.Button(button_frame, text="Save Encrypted Report")
        self.save_report_button.grid(row=3, column=0, sticky="ew", pady=3)

        self.open_report_button = ttk.Button(button_frame, text="Open Encrypted Report")
        self.open_report_button.grid(row=4, column=0, sticky="ew", pady=3)

        self.verify_button = ttk.Button(button_frame, text="Verify Report Integrity")
        self.verify_button.grid(row=5, column=0, sticky="ew", pady=3)

        output_frame = ttk.LabelFrame(content_frame, text="System Output", padding=10)
        output_frame.grid(row=0, column=1, sticky="nsew")
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)

        self.output_text = ScrolledText(output_frame, wrap="word", font=("Consolas", 10))
        self.output_text.grid(row=0, column=0, sticky="nsew")

        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(anchor="w", pady=(10, 0))

    def bind_actions(self, controller) -> None:
        self.load_dataset_button.configure(command=controller.load_dataset)
        self.evaluate_button.configure(command=controller.evaluate_student)
        self.generate_report_button.configure(command=controller.generate_report)
        self.save_report_button.configure(command=controller.save_encrypted_report)
        self.open_report_button.configure(command=controller.open_encrypted_report)
        self.verify_button.configure(command=controller.verify_current_report)

    def get_student_inputs(self) -> dict[str, str]:
        return {field: variable.get().strip() for field, variable in self.input_vars.items()}

    def set_categorical_options(self, options: dict[str, list[str]]) -> None:
        for field, values in options.items():
            widget = self.comboboxes[field]
            widget["values"] = values
            if values and not self.input_vars[field].get().strip():
                self.input_vars[field].set(values[0])

    def set_output(self, content: str) -> None:
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, content)

    def set_status(self, message: str) -> None:
        self.status_var.set(message)

    def ask_passphrase(self, prompt: str) -> str | None:
        return simpledialog.askstring("Passphrase", prompt, show="*", parent=self.root)

    def ask_open_report_path(self, initial_dir: Path) -> str:
        return filedialog.askopenfilename(
            title="Open Encrypted EduGuide Report",
            initialdir=str(initial_dir),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            parent=self.root,
        )

    def show_error(self, message: str) -> None:
        messagebox.showerror("EduGuide", message, parent=self.root)

    def show_info(self, message: str) -> None:
        messagebox.showinfo("EduGuide", message, parent=self.root)