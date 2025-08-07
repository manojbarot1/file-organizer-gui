#!/usr/bin/env python3
"""
A simple GUI application to identify file types and organize files into
type‑based folders.  It relies on the `filemagic` library (a ctypes
wrapper for libmagic) to detect each file's type and uses Tkinter for
the graphical interface.  All dependencies are open source.

Usage:
    python organizer.py

Selecting a folder will list all files along with their detected type in
the main window.  Clicking "Organize Files" will create subfolders based
on basic type categories and move the files accordingly.
"""

import os
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    # Use the python-magic package for file type detection.  This wrapper
    # automatically locates the libmagic shared library on most systems.
    import magic  # provided by the `python-magic` package
except ImportError as exc:
    raise RuntimeError(
        "The `python-magic` package is required for file type detection. "
        "Install it via `pip install python-magic`."
    ) from exc


def detect_file_type(file_path: Path) -> str:
    """Return a short description of the file's type using python-magic.

    The `python-magic` library wraps the libmagic functionality and exposes
    `magic.from_file` to obtain a human‑readable description of a file's
    contents.  If detection fails, ``Unknown`` is returned.
    """
    try:
        # `from_file` returns a textual description such as
        # "JPEG image data" or "PDF document".  We cast to str to guard
        # against unexpected non‑string return types.
        return str(magic.from_file(str(file_path)))
    except Exception:
        return "Unknown"


def assign_group(file_type: str) -> str:
    """Map a libmagic description to a higher‑level group folder name."""
    lower = file_type.lower()
    if any(keyword in lower for keyword in ["image", "jpeg", "png", "gif", "tiff"]):
        return "Images"
    if any(keyword in lower for keyword in ["pdf", "document", "word"]):
        return "Documents"
    if "text" in lower or "ascii" in lower:
        return "Text"
    if any(keyword in lower for keyword in ["audio", "mp3", "wav", "flac"]):
        return "Audio"
    if any(keyword in lower for keyword in ["video", "mp4", "avi", "mov"]):
        return "Video"
    if any(keyword in lower for keyword in ["zip", "archive", "compressed"]):
        return "Archives"
    return "Other"


class FileOrganizerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Type Organizer")
        self.geometry("700x500")
        self.selected_folder: Path | None = None
        self.files_info: list[tuple[str, str, str]] = []  # (file, type, group)
        self._build_widgets()

    def _build_widgets(self) -> None:
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Folder selection
        select_btn = ttk.Button(frame, text="Select Folder", command=self.select_folder)
        select_btn.pack(side=tk.TOP, pady=5)

        # Treeview for listing files
        columns = ("File", "Type", "Group")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Organize button
        org_btn = ttk.Button(frame, text="Organize Files", command=self.organize_files)
        org_btn.pack(side=tk.BOTTOM, pady=5)

    def select_folder(self) -> None:
        path = filedialog.askdirectory(title="Select folder to scan")
        if not path:
            return
        self.selected_folder = Path(path)
        self.scan_files()

    def scan_files(self) -> None:
        """Scan the selected folder for files and display their types."""
        if not self.selected_folder:
            return
        self.files_info.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for file_path in self.selected_folder.rglob("*"):
            if file_path.is_file():
                try:
                    ftype = detect_file_type(file_path)
                except Exception:
                    ftype = "Unknown"
                group = assign_group(ftype)
                relative_path = file_path.relative_to(self.selected_folder)
                self.files_info.append((str(relative_path), ftype, group))
                self.tree.insert("", tk.END, values=(relative_path, ftype, group))

    def organize_files(self) -> None:
        if not self.selected_folder or not self.files_info:
            messagebox.showinfo("No files", "Please select a folder and scan files first.")
            return
        # Confirm with the user
        if not messagebox.askyesno(
            "Confirm", "Create folders and move files? This will reorganize files."):
            return
        for rel_path, _ftype, group in self.files_info:
            src = self.selected_folder / rel_path
            target_dir = self.selected_folder / group
            target_dir.mkdir(exist_ok=True)
            dest = target_dir / src.name
            # If destination exists, append a counter
            counter = 1
            new_dest = dest
            while new_dest.exists():
                stem, suffix = os.path.splitext(src.name)
                new_name = f"{stem}_{counter}{suffix}"
                new_dest = target_dir / new_name
                counter += 1
            shutil.move(str(src), str(new_dest))
        messagebox.showinfo("Done", "Files have been organized.")
        self.scan_files()  # Refresh the listing


if __name__ == "__main__":
    app = FileOrganizerGUI()
    app.mainloop()