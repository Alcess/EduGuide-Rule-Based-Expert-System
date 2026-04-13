"""Tkinter interface for the EduGuide student advising application."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText


PALETTE = {
    "bg": "#f3eee7",
    "surface": "#fffaf4",
    "surface_alt": "#edf3ef",
    "hero": "#173f35",
    "accent": "#c96c37",
    "accent_active": "#b45e2f",
    "text": "#1f2933",
    "muted": "#58646b",
    "border": "#d6ccc0",
}


class ScrollablePage(tk.Frame):
    def __init__(self, parent: tk.Misc, background: str) -> None:
        super().__init__(parent, bg=background)

        self.canvas = tk.Canvas(self, bg=background, highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.content = tk.Frame(self.canvas, bg=background)
        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.content.bind("<Configure>", self._sync_scroll_region)
        self.canvas.bind("<Configure>", self._sync_window_width)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _sync_scroll_region(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _sync_window_width(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _bind_mousewheel(self, _event: tk.Event) -> None:
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event: tk.Event) -> None:
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class MainView:
    def __init__(self, root: tk.Tk, system_info: dict) -> None:
        self.root = root
        self.system_info = system_info

        self.root.title("EduGuide: Rule-Based Academic Advising Expert System")
        self.root.geometry("1240x820")
        self.root.minsize(1080, 720)
        self.root.configure(bg=PALETTE["bg"])

        self.input_vars: dict[str, tk.StringVar] = {}
        self.comboboxes: dict[str, ttk.Combobox] = {}
        self.output_text: ScrolledText | None = None
        self.status_var = tk.StringVar(
            value="Welcome to EduGuide. Review the system overview, then continue to the evaluation workspace."
        )

        self.start_evaluation_button: ttk.Button | None = None
        self.secondary_start_button: ttk.Button | None = None
        self.landing_info_button: ttk.Button | None = None
        self.landing_open_report_button: ttk.Button | None = None
        self.landing_exit_button: ttk.Button | None = None
        self.back_home_button: ttk.Button | None = None
        self.help_button: ttk.Button | None = None

        self.load_dataset_button: ttk.Button | None = None
        self.evaluate_button: ttk.Button | None = None
        self.generate_report_button: ttk.Button | None = None
        self.save_report_button: ttk.Button | None = None
        self.open_report_button: ttk.Button | None = None
        self.verify_button: ttk.Button | None = None

        self._configure_styles()
        self._build_layout()
        self.show_landing_page()

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Page.TFrame", background=PALETTE["bg"])
        style.configure(
            "Surface.TLabelframe",
            background=PALETTE["surface"],
            bordercolor=PALETTE["border"],
            relief="solid",
        )
        style.configure(
            "Surface.TLabelframe.Label",
            background=PALETTE["surface"],
            foreground=PALETTE["hero"],
            font=("Segoe UI", 11, "bold"),
        )
        style.configure("TLabel", background=PALETTE["bg"], foreground=PALETTE["text"], font=("Segoe UI", 10))
        style.configure(
            "Title.TLabel",
            background=PALETTE["bg"],
            foreground=PALETTE["hero"],
            font=("Georgia", 20, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=PALETTE["bg"],
            foreground=PALETTE["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Accent.TButton",
            background=PALETTE["accent"],
            foreground="#ffffff",
            borderwidth=0,
            focusthickness=0,
            padding=(16, 10),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Accent.TButton",
            background=[("active", PALETTE["accent_active"]), ("pressed", PALETTE["accent_active"])],
            foreground=[("disabled", "#f5e9df")],
        )
        style.configure(
            "Secondary.TButton",
            background=PALETTE["surface"],
            foreground=PALETTE["hero"],
            bordercolor=PALETTE["border"],
            padding=(14, 9),
            font=("Segoe UI", 10),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#f4ede2"), ("pressed", "#e9dfd0")],
            foreground=[("active", PALETTE["hero"])],
        )

    def _build_layout(self) -> None:
        self.page_container = tk.Frame(self.root, bg=PALETTE["bg"])
        self.page_container.pack(fill="both", expand=True)
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.landing_page = tk.Frame(self.page_container, bg=PALETTE["bg"])
        self.evaluation_page = ttk.Frame(self.page_container, padding=18, style="Page.TFrame")

        self.landing_page.grid(row=0, column=0, sticky="nsew")
        self.evaluation_page.grid(row=0, column=0, sticky="nsew")

        self._build_landing_page()
        self._build_evaluation_page()

        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            padding=(18, 8),
            style="Subtitle.TLabel",
        )
        status_bar.pack(fill="x")

    def _build_landing_page(self) -> None:
        scrollable = ScrollablePage(self.landing_page, background=PALETTE["bg"])
        scrollable.pack(fill="both", expand=True)

        content = scrollable.content
        content.grid_columnconfigure(0, weight=1)

        hero_frame = tk.Frame(
            content,
            bg=PALETTE["hero"],
            padx=30,
            pady=28,
            highlightbackground=PALETTE["border"],
            highlightthickness=1,
        )
        hero_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 14))
        hero_frame.grid_columnconfigure(0, weight=1)

        tk.Label(
            hero_frame,
            text=self.system_info["title"],
            bg=PALETTE["hero"],
            fg="#ffffff",
            font=("Georgia", 24, "bold"),
            anchor="w",
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            hero_frame,
            text=self.system_info["subtitle"],
            bg=PALETTE["hero"],
            fg="#d7e7df",
            font=("Segoe UI", 11),
            wraplength=980,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(10, 0))

        hero_actions = tk.Frame(hero_frame, bg=PALETTE["hero"])
        hero_actions.grid(row=2, column=0, sticky="w", pady=(22, 0))

        self.start_evaluation_button = ttk.Button(hero_actions, text="Start Evaluation", style="Accent.TButton")
        self.start_evaluation_button.grid(row=0, column=0, padx=(0, 10))

        self.landing_info_button = ttk.Button(
            hero_actions,
            text="View System Information / Help",
            style="Secondary.TButton",
        )
        self.landing_info_button.grid(row=0, column=1, padx=(0, 10))

        self.landing_open_report_button = ttk.Button(
            hero_actions,
            text="Open Saved Report",
            style="Secondary.TButton",
        )
        self.landing_open_report_button.grid(row=0, column=2, padx=(0, 10))

        self.landing_exit_button = ttk.Button(hero_actions, text="Exit", style="Secondary.TButton")
        self.landing_exit_button.grid(row=0, column=3)

        self._create_text_section(content, row=1, title="System Overview", body=self.system_info["overview"])

        variables_section = self._create_section_shell(content, row=2, title="Variables Used")
        tk.Label(
            variables_section,
            text=self.system_info["variables_intro"],
            bg=PALETTE["surface"],
            fg=PALETTE["muted"],
            font=("Segoe UI", 10),
            wraplength=980,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        variables_grid = tk.Frame(variables_section, bg=PALETTE["surface"])
        variables_grid.grid(row=1, column=0, sticky="ew", pady=(14, 0))
        variables_grid.grid_columnconfigure(0, weight=1)
        variables_grid.grid_columnconfigure(1, weight=1)

        for index, item in enumerate(self.system_info["variables"]):
            column = index % 2
            row = index // 2
            card = self._create_info_card(variables_grid, item["name"], item["description"])
            card.grid(row=row, column=column, sticky="nsew", padx=(0, 12) if column == 0 else (0, 0), pady=6)

        modules_section = self._create_section_shell(content, row=3, title="Main Modules / Functions")
        modules_grid = tk.Frame(modules_section, bg=PALETTE["surface"])
        modules_grid.grid(row=0, column=0, sticky="ew")
        modules_grid.grid_columnconfigure(0, weight=1)
        modules_grid.grid_columnconfigure(1, weight=1)

        for index, item in enumerate(self.system_info["modules"]):
            column = index % 2
            row = index // 2
            card = self._create_info_card(modules_grid, item["name"], item["description"], large=True)
            card.grid(row=row, column=column, sticky="nsew", padx=(0, 12) if column == 0 else (0, 0), pady=6)

        detail_row = tk.Frame(content, bg=PALETTE["bg"])
        detail_row.grid(row=4, column=0, sticky="ew", padx=20, pady=10)
        detail_row.grid_columnconfigure(0, weight=1)
        detail_row.grid_columnconfigure(1, weight=1)

        self._create_detail_card(
            detail_row,
            column=0,
            title="Rule-Based Expert System",
            body=self.system_info["rule_based_text"],
        )
        self._create_detail_card(
            detail_row,
            column=1,
            title="Security and Report Protection",
            body=self.system_info["security_text"],
        )

        workflow_section = self._create_section_shell(content, row=5, title="How to Proceed")
        tk.Label(
            workflow_section,
            text=self.system_info["workflow_intro"],
            bg=PALETTE["surface"],
            fg=PALETTE["muted"],
            font=("Segoe UI", 10),
            wraplength=980,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        steps_frame = tk.Frame(workflow_section, bg=PALETTE["surface_alt"], padx=18, pady=16)
        steps_frame.grid(row=1, column=0, sticky="ew", pady=(14, 0))
        for index, step in enumerate(self.system_info["workflow_steps"], start=1):
            tk.Label(
                steps_frame,
                text=f"{index}. {step}",
                bg=PALETTE["surface_alt"],
                fg=PALETTE["text"],
                font=("Segoe UI", 10),
                wraplength=960,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=3)

        footer_actions = tk.Frame(workflow_section, bg=PALETTE["surface"])
        footer_actions.grid(row=2, column=0, sticky="w", pady=(18, 0))

        self.secondary_start_button = ttk.Button(footer_actions, text="Start Evaluation", style="Accent.TButton")
        self.secondary_start_button.grid(row=0, column=0, padx=(0, 10))

        ttk.Button(
            footer_actions,
            text="Open Saved Report",
            style="Secondary.TButton",
            command=lambda: self.landing_open_report_button.invoke(),
        ).grid(row=0, column=1)

    def _build_evaluation_page(self) -> None:
        self.evaluation_page.columnconfigure(0, weight=1)
        self.evaluation_page.rowconfigure(1, weight=1)

        top_bar = ttk.Frame(self.evaluation_page, style="Page.TFrame")
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        top_bar.columnconfigure(0, weight=1)

        title_block = ttk.Frame(top_bar, style="Page.TFrame")
        title_block.grid(row=0, column=0, sticky="w")

        ttk.Label(title_block, text="Evaluation Workspace", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_block,
            text=(
                "Enter student values, evaluate risk, generate a report, then save or verify protected records "
                "without leaving the main window."
            ),
            style="Subtitle.TLabel",
            wraplength=760,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        nav_actions = ttk.Frame(top_bar, style="Page.TFrame")
        nav_actions.grid(row=0, column=1, sticky="e")

        self.help_button = ttk.Button(nav_actions, text="System Info", style="Secondary.TButton")
        self.help_button.grid(row=0, column=0, padx=(0, 10))

        self.back_home_button = ttk.Button(nav_actions, text="Back to Landing Page", style="Secondary.TButton")
        self.back_home_button.grid(row=0, column=1)

        content_frame = ttk.Frame(self.evaluation_page, style="Page.TFrame")
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.columnconfigure(0, weight=0)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)

        input_frame = ttk.LabelFrame(content_frame, text="Student Input", padding=16, style="Surface.TLabelframe")
        input_frame.grid(row=0, column=0, sticky="nsw", padx=(0, 14))

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
                widget = ttk.Combobox(input_frame, textvariable=variable, state="readonly", width=22)
                widget.grid(row=row_index, column=1, sticky="ew", pady=4)
                self.comboboxes[field_name] = widget
            else:
                widget = ttk.Entry(input_frame, textvariable=variable, width=24)
                widget.grid(row=row_index, column=1, sticky="ew", pady=4)

        input_frame.columnconfigure(1, weight=1)

        button_frame = ttk.LabelFrame(input_frame, text="Actions", padding=12, style="Surface.TLabelframe")
        button_frame.grid(row=len(field_specs), column=0, columnspan=2, sticky="ew", pady=(16, 0))
        button_frame.columnconfigure(0, weight=1)

        self.load_dataset_button = ttk.Button(button_frame, text="Load Dataset", style="Secondary.TButton")
        self.load_dataset_button.grid(row=0, column=0, sticky="ew", pady=3)

        self.evaluate_button = ttk.Button(button_frame, text="Evaluate Student", style="Accent.TButton")
        self.evaluate_button.grid(row=1, column=0, sticky="ew", pady=3)

        self.generate_report_button = ttk.Button(button_frame, text="Generate Report", style="Secondary.TButton")
        self.generate_report_button.grid(row=2, column=0, sticky="ew", pady=3)

        self.save_report_button = ttk.Button(button_frame, text="Save Encrypted Report", style="Secondary.TButton")
        self.save_report_button.grid(row=3, column=0, sticky="ew", pady=3)

        self.open_report_button = ttk.Button(button_frame, text="Open Encrypted Report", style="Secondary.TButton")
        self.open_report_button.grid(row=4, column=0, sticky="ew", pady=3)

        self.verify_button = ttk.Button(button_frame, text="Verify Report Integrity", style="Secondary.TButton")
        self.verify_button.grid(row=5, column=0, sticky="ew", pady=3)

        output_frame = ttk.LabelFrame(content_frame, text="System Output", padding=12, style="Surface.TLabelframe")
        output_frame.grid(row=0, column=1, sticky="nsew")
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)

        self.output_text = ScrolledText(
            output_frame,
            wrap="word",
            font=("Consolas", 10),
            padx=10,
            pady=10,
            relief="flat",
            borderwidth=0,
            background="#fffdf9",
            foreground=PALETTE["text"],
        )
        self.output_text.grid(row=0, column=0, sticky="nsew")

    def _create_text_section(self, parent: tk.Frame, row: int, title: str, body: str) -> None:
        section = self._create_section_shell(parent, row=row, title=title)
        tk.Label(
            section,
            text=body,
            bg=PALETTE["surface"],
            fg=PALETTE["text"],
            font=("Segoe UI", 10),
            wraplength=980,
            justify="left",
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

    def _create_section_shell(self, parent: tk.Frame, row: int, title: str) -> tk.Frame:
        outer = tk.Frame(
            parent,
            bg=PALETTE["surface"],
            padx=24,
            pady=22,
            highlightbackground=PALETTE["border"],
            highlightthickness=1,
        )
        outer.grid(row=row, column=0, sticky="ew", padx=20, pady=10)
        outer.grid_columnconfigure(0, weight=1)

        tk.Label(
            outer,
            text=title,
            bg=PALETTE["surface"],
            fg=PALETTE["hero"],
            font=("Georgia", 16, "bold"),
            anchor="w",
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        inner = tk.Frame(outer, bg=PALETTE["surface"])
        inner.grid(row=1, column=0, sticky="ew")
        inner.grid_columnconfigure(0, weight=1)
        return inner

    def _create_info_card(self, parent: tk.Frame, title: str, body: str, large: bool = False) -> tk.Frame:
        card = tk.Frame(
            parent,
            bg=PALETTE["surface_alt"],
            padx=16,
            pady=14,
            highlightbackground=PALETTE["border"],
            highlightthickness=1,
        )
        tk.Label(
            card,
            text=title,
            bg=PALETTE["surface_alt"],
            fg=PALETTE["hero"],
            font=("Segoe UI", 11, "bold"),
            anchor="w",
            justify="left",
        ).pack(anchor="w")
        tk.Label(
            card,
            text=body,
            bg=PALETTE["surface_alt"],
            fg=PALETTE["text"],
            font=("Segoe UI", 10),
            wraplength=430 if large else 410,
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(8, 0))
        return card

    def _create_detail_card(self, parent: tk.Frame, column: int, title: str, body: str) -> None:
        card = tk.Frame(
            parent,
            bg=PALETTE["surface"],
            padx=24,
            pady=22,
            highlightbackground=PALETTE["border"],
            highlightthickness=1,
        )
        card.grid(row=0, column=column, sticky="nsew", padx=(0, 12) if column == 0 else (0, 0))

        tk.Label(
            card,
            text=title,
            bg=PALETTE["surface"],
            fg=PALETTE["hero"],
            font=("Georgia", 15, "bold"),
            anchor="w",
            justify="left",
        ).pack(anchor="w")
        tk.Label(
            card,
            text=body,
            bg=PALETTE["surface"],
            fg=PALETTE["text"],
            font=("Segoe UI", 10),
            wraplength=455,
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(10, 0))

    def bind_actions(self, controller) -> None:
        self.start_evaluation_button.configure(command=controller.show_evaluation_page)
        self.secondary_start_button.configure(command=controller.show_evaluation_page)
        self.landing_info_button.configure(command=controller.show_help)
        self.landing_open_report_button.configure(command=controller.open_encrypted_report)
        self.landing_exit_button.configure(command=self.root.destroy)
        self.back_home_button.configure(command=controller.show_landing_page)
        self.help_button.configure(command=controller.show_help)

        self.load_dataset_button.configure(command=controller.load_dataset)
        self.evaluate_button.configure(command=controller.evaluate_student)
        self.generate_report_button.configure(command=controller.generate_report)
        self.save_report_button.configure(command=controller.save_encrypted_report)
        self.open_report_button.configure(command=controller.open_encrypted_report)
        self.verify_button.configure(command=controller.verify_current_report)

    def show_landing_page(self) -> None:
        self.landing_page.tkraise()

    def show_evaluation_page(self) -> None:
        self.evaluation_page.tkraise()

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

    def show_text_dialog(self, title: str, content: str) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("760x560")
        dialog.minsize(620, 460)
        dialog.configure(bg=PALETTE["bg"])
        dialog.transient(self.root)

        wrapper = ttk.Frame(dialog, padding=16, style="Page.TFrame")
        wrapper.pack(fill="both", expand=True)
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(1, weight=1)

        ttk.Label(wrapper, text=title, style="Title.TLabel").grid(row=0, column=0, sticky="w")

        body = ScrolledText(
            wrapper,
            wrap="word",
            font=("Segoe UI", 10),
            padx=12,
            pady=12,
            relief="flat",
            borderwidth=0,
            background="#fffdf9",
            foreground=PALETTE["text"],
        )
        body.grid(row=1, column=0, sticky="nsew", pady=(12, 12))
        body.insert("1.0", content)
        body.configure(state="disabled")

        ttk.Button(wrapper, text="Close", style="Secondary.TButton", command=dialog.destroy).grid(
            row=2,
            column=0,
            sticky="e",
        )

        dialog.grab_set()
        dialog.focus_set()