"""Entry point for the EduGuide desktop prototype."""

from __future__ import annotations

import tkinter as tk

from controllers.app_controller import AppController


def main() -> None:
    root = tk.Tk()
    AppController(root)
    root.mainloop()


if __name__ == "__main__":
    main()