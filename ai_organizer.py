#!/usr/bin/env python3
import os
import re
import json
import csv
import time
import shutil
import threading
import tempfile
import difflib
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Iterable
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from ai_backends import (
    query_ollama,
    query_openai,
    query_grok,
    list_ollama_models,
    test_ai_connection,
    optimize_prompt_for_backend,
)


AI_BACKENDS = ["Local (Ollama)", "OpenAI", "Grok"]

HISTORY_FILE = "organizer_history.json"
RULES_FILE = "organizer_rules.json"
DEFAULT_MAX_WORKERS = max(4, os.cpu_count() or 4)

TERRAFORM_SUBPATH = Path("infrastructure/terraform")
PROJECT_MARKERS = {".git", "package.json", "go.mod", "pyproject.toml", "main.tf"}
TF_EXTS = {".tf", ".tfvars", ".tfstate", ".lock.hcl"}


class OrganizerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("AI File Organizer")
        self.geometry("1160x780")
        self.minsize(960, 660)

        self.scanning = False
        self.cancel_event = threading.Event()
        self.current_futures = set()
        self.executor = ThreadPoolExecutor(max_workers=DEFAULT_MAX_WORKERS)

        self.folder: Optional[Path] = None
        self.root_name: str = ""
        self.is_project: bool = False
        self.has_terraform: bool = False

        self.file_items: List[Tuple[Path, str, tk.BooleanVar, str]] = []
        self.model_list: List[str] = []
        self.history: Dict[str, dict] = {}
        self.rules: Dict[str, str] = {}

        self._load_history()
        self._load_rules()

        self.selected_backend = tk.StringVar(value=AI_BACKENDS[0])
        self.selected_model = tk.StringVar(value="")
        self.api_key = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Select a folder to start.")
        self.progress_var = tk.IntVar(value=0)
        self.select_all_var = tk.BooleanVar(value=False)

        self.stay_under_root_var = tk.BooleanVar(value=True)
        self.pin_terraform_var = tk.BooleanVar(value=True)
        self.prefer_folder_move_var = tk.BooleanVar(value=True)

        self.ignore_cache_this_run = False
        self.refine_two_pass_var = tk.BooleanVar(value=True)

        self.tmp_scan_path: Optional[Path] = None
        self.tmp_lock = threading.Lock()

        # dynamic directory map for snapping
        self._dir_children: Dict[Path, List[str]] = {}

        self._build_ui()
        self._on_backend_change()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------- UI -------------------------------
    def _build_ui(self):
        top = ttk.Frame(self); top.pack(side=tk.TOP, fill=tk.X, padx=12, pady=8)
        ttk.Button(top, text="Select Folder", command=self._on_choose_folder).pack(side=tk.LEFT, padx=(0,8))
        self.folder_lbl = ttk.Label(top, text="(none)"); self.folder_lbl.pack(side=tk.LEFT, padx=(0,12))
        ttk.Button(top, text="Scan with AI", command=self._on_scan).pack(side=tk.LEFT, padx=(0,8))
        ttk.Button(top, text="Rescan (fresh AI)", command=self._on_rescan_fresh).pack(side=tk.LEFT, padx=(0,8))
        ttk.Button(top, text="Clear on‑disk cache", command=self._on_clear_cache).pack(side=tk.LEFT, padx=(0,8))
        ttk.Button(top, text="Cancel Scan", command=self._on_cancel_scan).pack(side=tk.LEFT, padx=(0,8))

        cfg = ttk.Frame(self); cfg.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(0,6))
        ttk.Label(cfg, text="Backend:").pack(side=tk.LEFT)
        self.backend_cb = ttk.Combobox(cfg, textvariable=self.selected_backend, values=AI_BACKENDS, width=16, state="readonly")
        self.backend_cb.bind("<<ComboboxSelected>>", lambda e: self._on_backend_change())
        self.backend_cb.pack(side=tk.LEFT, padx=(6,12))

        ttk.Label(cfg, text="Model:").pack(side=tk.LEFT)
        self.model_cb = ttk.Combobox(cfg, textvariable=self.selected_model, values=self.model_list, width=22)
        self.model_cb.pack(side=tk.LEFT, padx=(6,12))

        ttk.Label(cfg, text="API Key:").pack(side=tk.LEFT)
        self.api_entry = ttk.Entry(cfg, textvariable=self.api_key, show="•", width=30)
        self.api_entry.pack(side=tk.LEFT, padx=(6,6))
        ttk.Button(cfg, text="Test", command=self._on_test_ai).pack(side=tk.LEFT, padx=(2,12))

        ttk.Checkbutton(cfg, text="Refine suggestion (two‑pass)", variable=self.refine_two_pass_var).pack(side=tk.LEFT, padx=(0,12))
        ttk.Checkbutton(cfg, text="Select All", variable=self.select_all_var, command=self._on_select_all).pack(side=tk.LEFT, padx=(0,12))
        ttk.Checkbutton(cfg, text="Stay under root", variable=self.stay_under_root_var).pack(side=tk.LEFT, padx=(0,10))
        ttk.Checkbutton(cfg, text="Pin Terraform", variable=self.pin_terraform_var).pack(side=tk.LEFT, padx=(0,10))
        ttk.Checkbutton(cfg, text="Prefer folder move", variable=self.prefer_folder_move_var).pack(side=tk.LEFT, padx=(0,10))

        tree_frame = ttk.Frame(self); tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=6)
        columns = ("Select", "Source Path", "Target Path", "Status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("Select", text="✓"); self.tree.column("Select", width=50, anchor=tk.CENTER, stretch=False)
        self.tree.heading("Source Path", text="Source Path"); self.tree.column("Source Path", width=620, anchor=tk.W, stretch=True)
        self.tree.heading("Target Path", text="Target Organization Path"); self.tree.column("Target Path", width=620, anchor=tk.W, stretch=True)
        self.tree.heading("Status", text="Status"); self.tree.column("Status", width=200, anchor=tk.W, stretch=False)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y); self.tree.configure(yscrollcommand=y_scroll.set)
        x_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X); self.tree.configure(xscrollcommand=x_scroll.set)

        act = ttk.Frame(self); act.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=8)
        self.progress = ttk.Progressbar(act, orient=tk.HORIZONTAL, mode="determinate", maximum=100, variable=self.progress_var)
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,8))
        ttk.Label(act, textvariable=self.status_var).pack(side=tk.LEFT)

        exp = ttk.Frame(self); exp.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0,8))
        ttk.Button(exp, text="Export List", command=self._on_export_list).pack(side=tk.LEFT)
        ttk.Button(exp, text="Organize", command=self._on_organize).pack(side=tk.LEFT, padx=(8,0))

    # ---------------------------- Events ----------------------------
    def _on_choose_folder(self):
        folder = filedialog.askdirectory(title="Choose a folder to scan")
        if not folder:
            return
        self.folder = Path(folder)
        self.root_name = self.folder.name
        self.folder_lbl.configure(text=str(self.folder))
        self.status_var.set("Ready.")
        self.is_project, self.has_terraform = self._detect_project(self.folder)
        self._build_dir_children()
        self._clear_tree()

    def _on_backend_change(self):
        backend = self.selected_backend.get()
        if backend == "Local (Ollama)":
            try:
                models = list_ollama_models()
            except Exception:
                models = []
            self.model_list = models
            self.model_cb.configure(values=models, state="readonly")
            if models and (self.selected_model.get() not in models):
                self.selected_model.set(models[0])
        else:
            self.model_list = []
            self.model_cb.configure(values=[], state="normal")

    def _on_test_ai(self):
        ok, msg = test_ai_connection(self.selected_backend.get(), self.selected_model.get().strip(), self.api_key.get().strip())
        if ok:
            messagebox.showinfo("AI Connection", msg or "OK")
        else:
            messagebox.showerror("AI Connection", msg or "Failed")

    def _on_scan(self):
        self.ignore_cache_this_run = False
        self._start_scan()

    def _on_rescan_fresh(self):
        if not self.folder:
            messagebox.showwarning("No folder", "Please choose a folder first.")
            return
        self._clear_tree()
        self.ignore_cache_this_run = True
        self._start_scan()

    def _on_clear_cache(self):
        if os.path.exists(HISTORY_FILE):
            try:
                os.remove(HISTORY_FILE)
                self.history = {}
                messagebox.showinfo("Cache cleared", "Deleted organizer_history.json and reset cache.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete cache file: {e}")
        else:
            self.history = {}
            messagebox.showinfo("Cache cleared", "No cache file found; in‑memory cache reset.")

    def _start_scan(self):
        if not self.folder:
            messagebox.showwarning("No folder", "Please choose a folder first.")
            return
        if self.scanning:
            return
        try:
            tmpdir = Path(tempfile.gettempdir())
            self.tmp_scan_path = tmpdir / f"ai_scan_{int(time.time())}.jsonl"
        except Exception:
            self.tmp_scan_path = None

        self.scanning = True
        self.cancel_event.clear()
        self.current_futures.clear()
        self.progress_var.set(0)
        self.status_var.set("Scanning...")
        threading.Thread(target=self._scan_folder_async, daemon=True).start()

    def _on_cancel_scan(self):
        if not self.scanning:
            return
        self.scanning = False
        self.cancel_event.set()
        for fut in list(self.current_futures):
            fut.cancel()
        self.status_var.set("Cancelling scan...")

    def _on_select_all(self):
        v = self.select_all_var.get()
        for (_, _, checked, _) in self.file_items:
            checked.set(v)

    def _on_organize(self):
        sel = [(s, t, c, st) for (s, t, c, st) in self.file_items if c.get()]
        if not sel:
            messagebox.showinfo("Nothing to organize", "Select at least one item.")
            return
        dest = filedialog.askdirectory(title="Choose destination root")
        if not dest:
            return
        self.progress_var.set(0)
        self.status_var.set("Organizing...")
        self._organize_files_async(sel, Path(dest))

    def _on_export_list(self):
        if not self.file_items:
            messagebox.showinfo("Nothing to export", "Scan first.")
            return
        path = filedialog.asksaveasfilename(title="Export list to CSV", defaultextension=".csv", filetypes=[("CSV", "*.csv"), ("All Files", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["checked", "source", "target", "status"])
                for (src, tgt, chk, st) in self.file_items:
                    w.writerow([bool(chk.get()), str(src), tgt, st])
            messagebox.showinfo("Exported", f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Export error", str(e))

    # -------------------------- Scan / AI ---------------------------
    def _scan_folder_async(self):
        try:
            files: List[Path] = []
            for root, _, names in os.walk(self.folder):
                if self.cancel_event.is_set():
                    break
                for n in names:
                    if n.startswith(".DS_Store") or n.startswith("._"):
                        continue
                    files.append(Path(root) / n)

            total = max(1, len(files))
            backend = self.selected_backend.get()
            model = self.selected_model.get().strip()
            api_key = self.api_key.get().strip()
            refine = self.refine_two_pass_var.get()

            future_to_file: Dict = {}
            for f in files:
                if not self.scanning or self.cancel_event.is_set():
                    break
                fut = self.executor.submit(self._process_file_two_pass, f, backend, model, api_key, self.ignore_cache_this_run, refine)
                self.current_futures.add(fut)
                future_to_file[fut] = f

            completed = 0
            for fut in as_completed(future_to_file):
                if not self.scanning or self.cancel_event.is_set():
                    break
                src = future_to_file[fut]
                try:
                    final_path, status = fut.result()
                except Exception as e:
                    final_path, status = "Uncategorized", f"Error: {e}"
                checked = tk.BooleanVar(value=True)
                entry = (src, final_path, checked, status)
                self.file_items.append(entry)
                completed += 1
                progress = int((completed * 100) / total)
                self.after(0, lambda e=entry: self._add_file_to_tree(e))
                self.after(0, lambda p=progress: self.progress_var.set(p))
                self.after(0, lambda c=completed, t=total: self.status_var.set(f"Scanning... {c}/{t}"))

            for fut in future_to_file:
                if not fut.done():
                    fut.cancel()
            self.current_futures.difference_update(future_to_file.keys())
        finally:
            self.after(0, self._finish_scan)

    def _finish_scan(self):
        self.scanning = False
        self.progress_var.set(0)
        self.status_var.set("Scan cancelled." if self.cancel_event.is_set() else "Scan complete.")
        self.ignore_cache_this_run = False

    # --------------------- Two‑pass worker -------------------------
    def _process_file_two_pass(self, file_path: Path, backend: str, model: str, api_key: str, ignore_cache: bool, refine: bool) -> Tuple[str, str]:
        if self.cancel_event.is_set():
            return "Uncategorized", "Cancelled"
        sig = self._signature(file_path)
        hint = self._build_file_hint(file_path)
        taxonomy = self._build_taxonomy_prompt(max_parents=12, max_children=8)
        neighbor = self._build_neighbor_context(file_path, max_siblings=12)

        # First pass
        if not ignore_cache and sig in self.history:
            first_path = self.history[sig].get("ai_path", "Uncategorized")
            first_src = "Cached"
        else:
            base_prompt = (
                "Return ONLY a relative folder path (1-3 levels) to organize the file. "
                "Prefer EXISTING folders from the taxonomy below. If a close synonym exists, use the existing folder name (do not invent new top-level names).\n"
                f"Root: {self.root_name}\n\n"
                f"Existing taxonomy (samples):\n{taxonomy}\n\n"
                f"File: {file_path.name}\n{hint}\n\n"
                f"Neighbor context:\n{neighbor}\n\n"
                "Rules:\n- Output ONLY the path on one line\n- Use forward slashes\n- Max depth 3\n- If uncertain, reply 'Uncategorized'\n"
            )
            prompt = optimize_prompt_for_backend(backend, base_prompt)
            try:
                if backend == "Local (Ollama)":
                    text = query_ollama(model=model or "llama3.1", prompt=prompt)
                elif backend == "OpenAI":
                    text = query_openai(model=model or "gpt-4o-mini", prompt=prompt, api_key=api_key)
                elif backend == "Grok":
                    text = query_grok(model=model or "grok-2-mini", prompt=prompt, api_key=api_key)
                else:
                    text = "Uncategorized"
            except Exception:
                text = "Uncategorized"
            first_path = self._apply_guardrails(file_path, text)
            first_src = "AI suggested"

        self._append_temp_log({"ts": time.time(), "source": str(file_path), "hint": hint, "first_path": first_path, "refined_path": None, "status": first_src})

        if self.cancel_event.is_set():
            return "Uncategorized", "Cancelled"

        if refine:
            refine_prompt = (
                "Given a candidate folder path, improve it ONLY if it conflicts with the existing taxonomy; otherwise return it unchanged.\n"
                "Output ONLY the path. Max depth 3. Prefer existing folder names from the taxonomy.\n"
                f"Root: {self.root_name}\n\nExisting taxonomy (samples):\n{taxonomy}\n\n"
                f"Filename: {file_path.name}\n{hint}\nCandidate: {first_path}\n"
            )
            prompt2 = optimize_prompt_for_backend(backend, refine_prompt)
            try:
                if backend == "Local (Ollama)":
                    text2 = query_ollama(model=model or "llama3.1", prompt=prompt2)
                elif backend == "OpenAI":
                    text2 = query_openai(model=model or "gpt-4o-mini", prompt=prompt2, api_key=api_key)
                elif backend == "Grok":
                    text2 = query_grok(model=model or "grok-2-mini", prompt=prompt2, api_key=api_key)
                else:
                    text2 = first_path
            except Exception:
                text2 = first_path
            refined_path = self._apply_guardrails(file_path, text2)
            final_path = refined_path or first_path
            status = f"{first_src} → Refined"
        else:
            final_path = first_path
            status = first_src

        self.history[sig] = {"ai_path": final_path, "fullpath": str(file_path), "timestamp": time.time()}
        self._save_history()
        self._append_temp_log({"ts": time.time(), "source": str(file_path), "hint": hint, "first_path": first_path, "refined_path": final_path if refine else None, "status": status})
        return final_path, status

    # ---------------- Parsing & Guardrails -------------------------
    def _extract_path_from_text(self, text: str) -> str:
        if not text:
            return ""
        m = re.search(r'{\s*"path"\s*:\s*"([^"]+)"}', text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"^#+\s.*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"\b(the cleaned compact path would be|the path would be|the best path is|final path:)\b.*", "", text, flags=re.IGNORECASE)
        candidates = re.findall(r"([A-Za-z0-9 _.-]+(?:/[A-Za-z0-9 _.-]+){0,2})", text)

        def score(c: str) -> int:
            c_stripped = c.strip().strip("./ ")
            penalty = 0
            if re.search(r"\b(is|are|the|this|that|here|would)\b", c_stripped, flags=re.IGNORECASE):
                penalty += 2
            if len(c_stripped.split()) > 6:
                penalty += 3
            segs = [s for s in c_stripped.split("/") if s]
            base = 10 - min(9, len("".join(segs)))
            return base - penalty

        candidates = [c.strip() for c in candidates if ("/" in c) or (len(c.split()) <= 4)]
        if not candidates:
            return ""
        best = max(candidates, key=score).strip().strip("./ ")
        best = re.sub(r"\s{2,}", " ", best)
        best = re.sub(r"/{2,}", "/", best)
        parts = [p.strip() for p in best.split("/") if p.strip()]
        return "/".join(parts[:3])

    def _sanitize_path(self, text: str) -> str:
        extracted = self._extract_path_from_text(text)
        candidate = extracted if extracted else (text or "")
        candidate = candidate.strip().replace("\\", "/").splitlines()[0].lstrip("/").strip()
        for ch in '<>:"|?*':
            candidate = candidate.replace(ch, "")
        if not candidate:
            candidate = "Uncategorized"
        parts = [p for p in candidate.split("/") if p]
        if len(parts) > 3:
            parts = parts[:3]
        return "/".join(parts)

    def _apply_guardrails(self, file_path: Path, ai_path: str) -> str:
        rel = self._sanitize_path(ai_path)
        if self.pin_terraform_var.get() and (file_path.suffix.lower() in TF_EXTS or file_path.name.endswith(".lock.hcl")):
            pinned = Path(self.root_name) / TERRAFORM_SUBPATH
            return str(pinned)
        if self.stay_under_root_var.get() and not self._starts_with_root(rel):
            rel = str(Path(self.root_name) / rel)
        # snap segments to existing directories to honor local taxonomy
        try:
            rel = self._snap_to_existing_dirs(rel)
        except Exception:
            pass
        return rel

    def _starts_with_root(self, rel: str) -> bool:
        parts = [p for p in str(rel).strip("/").split("/") if p]
        return (len(parts) > 0) and (parts[0].lower() == self.root_name.lower())

    # -------------------- Context builders -------------------------
    def _build_file_hint(self, p: Path) -> str:
        ext = p.suffix.lower()
        parent = p.parent.name
        name = p.name
        ancestors = "/".join([a.name for a in p.parents if a != p.anchor and a != p] [-4:][::-1])
        if ext in {".jpg", ".jpeg", ".png", ".heic", ".webp", ".tif", ".tiff"}:
            try:
                size = p.stat().st_size
            except Exception:
                size = 0
            return f"Type=Image; SizeBytes={size}; Name={name}; Parent={parent}; Ancestors={ancestors}"
        if ext in {".mp3", ".m4a", ".flac", ".wav", ".aac", ".ogg"}:
            try:
                size = p.stat().st_size
            except Exception:
                size = 0
            return f"Type=Audio; SizeBytes={size}; Name={name}; Parent={parent}; Ancestors={ancestors}"
        if ext in {".mp4", ".mov", ".mkv", ".avi", ".webm"}:
            try:
                size = p.stat().st_size
            except Exception:
                size = 0
            return f"Type=Video; SizeBytes={size}; Name={name}; Parent={parent}; Ancestors={ancestors}"
        if ext in {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".md", ".txt", ".rtf"}:
            return f"Type=Doc; Name={name}; Parent={parent}; Ancestors={ancestors}"
        if ext in TF_EXTS or p.name.endswith(".lock.hcl"):
            return f"Type=Terraform; Name={name}; Parent={parent}; Ancestors={ancestors}"
        return f"Filename={name}; Parent={parent}; Ancestors={ancestors}; Ext={ext or '(none)'}"

    def _build_taxonomy_prompt(self, max_parents: int = 10, max_children: int = 8) -> str:
        if not self.folder:
            return ""
        lines: List[str] = []
        parents = sorted([p for p in self.folder.iterdir() if p.is_dir()], key=lambda x: x.name.lower())[:max_parents]
        for par in parents:
            try:
                kids = sorted([c.name for c in par.iterdir() if c.is_dir()], key=lambda x: x.lower())[:max_children]
            except Exception:
                kids = []
            if kids:
                lines.append(f"- {par.name}/ -> {', '.join(kids)}")
            else:
                lines.append(f"- {par.name}/")
        return "\n".join(lines) if lines else "(no subfolders yet)"

    def _build_neighbor_context(self, p: Path, max_siblings: int = 15) -> str:
        try:
            sibs = [c.name for c in p.parent.iterdir() if c.is_file()][:max_siblings]
        except Exception:
            sibs = []
        try:
            dirs = [c.name for c in p.parent.iterdir() if c.is_dir()][:max_siblings]
        except Exception:
            dirs = []
        return f"ParentDir={p.parent.name}; SiblingDirs={', '.join(dirs)}; SiblingFiles={', '.join(sibs)}"

    # ------------------- Organize (folder-smart) -------------------
    def _organize_files_async(self, selected_files, dest_path: Path):
        def top_app_bundle(pp: Path) -> Optional[Path]:
            for anc in (pp,) + tuple(pp.parents):
                if anc.suffix.lower() == ".app":
                    return anc
            return None

        def maj_prefix(paths: List[str], k: int = 2) -> Tuple[str, ...]:
            cleaned = [tuple(Path(p).parts[:k]) for p in paths if p]
            if not cleaned:
                return ()
            return Counter(cleaned).most_common(1)[0][0]

        def organize():
            success = errors = 0
            groups: Dict[Path, List[Tuple[Path, str]]] = defaultdict(list)
            for src, tgt, chk, _ in selected_files:
                if not chk.get():
                    continue
                root = top_app_bundle(src) or src.parent
                groups[root].append((src, tgt))

            folder_moves: Dict[Path, Path] = {}
            for src_dir, items in groups.items():
                tgts = [t for _, t in items]
                counts = Counter(tuple(Path(t).parts[:2]) for t in tgts if t)
                agree = (counts.most_common(1)[0][1] / len(tgts)) if tgts else 0.0
                if (self.prefer_folder_move_var.get() and self.is_project) or src_dir.suffix.lower() == ".app" or (len(items) > 4 and agree >= 0.6):
                    base = Path(*maj_prefix(tgts, k=2)) if tgts else Path(self.root_name if self.stay_under_root_var.get() else "Uncategorized")
                    if self.stay_under_root_var.get():
                        if not (len(base.parts) > 0 and base.parts[0].lower() == self.root_name.lower()):
                            base = Path(self.root_name) / base
                    folder_moves[src_dir] = dest_path / base / src_dir.name

            for src_dir, dst_dir in folder_moves.items():
                try:
                    dst_dir.parent.mkdir(parents=True, exist_ok=True)
                    candidate = dst_dir; i = 1
                    while candidate.exists():
                        candidate = dst_dir.with_name(f"{dst_dir.name}_{i}"); i += 1
                    shutil.move(str(src_dir), str(candidate))
                    success += 1
                except Exception as e:
                    print(f"Error moving folder {src_dir}: {e}"); errors += 1

            moved_roots = set(folder_moves.keys())
            remaining = [(s, t) for (s, t, c, _) in selected_files if c.get() and not any(s == r or r in s.parents for r in moved_roots)]
            total = max(1, len(remaining))
            for i, (src, tgt) in enumerate(remaining):
                try:
                    tpath = Path(tgt)
                    if self.stay_under_root_var.get():
                        if not (len(tpath.parts) > 0 and tpath.parts[0].lower() == self.root_name.lower()):
                            tpath = Path(self.root_name) / tpath
                    tdir = dest_path / tpath
                    tdir.mkdir(parents=True, exist_ok=True)
                    target = tdir / src.name
                    n = 1
                    while target.exists():
                        target = tdir / f"{src.stem}_{n}{src.suffix}"; n += 1
                    shutil.move(str(src), str(target))
                    success += 1
                except Exception as e:
                    print(f"Error organizing {src}: {e}"); errors += 1
                prog = int((i + 1) * 100 / total)
                self.after(0, lambda p=prog: self.progress_var.set(p))
                self.after(0, lambda s=success, e=errors: self.status_var.set(f"Organizing... Success: {s}, Errors: {e}"))

            self.after(0, lambda: self.progress_var.set(0))
            self.after(0, lambda: self.status_var.set(f"Organization complete! Success: {success}, Errors: {errors}"))
            if errors == 0:
                self.after(0, lambda: messagebox.showinfo("Success", f"All {success} item(s) organized!"))
            else:
                self.after(0, lambda: messagebox.showwarning("Completed with Errors", f"Organized {success} item(s), {errors} failed."))

        threading.Thread(target=organize, daemon=True).start()

    # ------------------------ Temp Log -----------------------------
    def _append_temp_log(self, obj: dict):
        if not self.tmp_scan_path:
            return
        line = json.dumps(obj, ensure_ascii=False)
        with self.tmp_lock:
            try:
                with open(self.tmp_scan_path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception:
                pass

    # ------------------------ Tree UI ------------------------------
    def _add_file_to_tree(self, entry: Tuple[Path, str, tk.BooleanVar, str]):
        src, ai_path, checked, status = entry
        checkbox = "☑" if checked.get() else "☐"
        iid = self.tree.insert("", "end", values=(checkbox, str(src), ai_path, status))
        try:
            self.tree.see(iid); self.tree.yview_moveto(1.0)
        except tk.TclError:
            pass

        def _sync(*_):
            try:
                self.tree.set(iid, "Select", "☑" if checked.get() else "☐")
            except tk.TclError:
                pass
        checked.trace_add("write", _sync)

    def _clear_tree(self):
        self.file_items.clear()
        for iid in self.tree.get_children():
            self.tree.delete(iid)

    # ----------------------- Helpers/State -------------------------
    def _signature(self, p: Path) -> str:
        try:
            st = p.stat()
            return f"{p.name}|{st.st_size}|{int(st.st_mtime)}"
        except Exception:
            return f"{p.name}|0|0"

    def _detect_project(self, root: Path) -> Tuple[bool, bool]:
        found_markers = False
        has_tf = False
        try:
            entries = set(os.listdir(root))
            if entries & PROJECT_MARKERS:
                found_markers = True
            for dirpath, _, filenames in os.walk(root):
                for n in filenames:
                    if n.endswith(".tf") or n.endswith(".tfvars") or n.endswith(".tfstate") or n.endswith(".lock.hcl"):
                        has_tf = True
                        break
                if has_tf:
                    break
        except Exception:
            pass
        return found_markers, has_tf

    def _load_history(self):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except Exception:
            self.history = {}

    def _save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f)
        except Exception:
            pass

    def _load_rules(self):
        try:
            with open(RULES_FILE, "r", encoding="utf-8") as f:
                self.rules = json.load(f)
        except Exception:
            self.rules = {}

    # ----------------------- Dir map & snapping --------------------
    def _build_dir_children(self):
        self._dir_children.clear()
        if not self.folder:
            return
        for root, dirs, _ in os.walk(self.folder):
            parent = Path(root)
            try:
                self._dir_children[parent] = list(dirs)
            except Exception:
                self._dir_children[parent] = []

    def _iter_children(self, parent: Path) -> Iterable[str]:
        if parent in self._dir_children:
            return self._dir_children[parent]
        try:
            names = [p.name for p in parent.iterdir() if p.is_dir()]
        except Exception:
            names = []
        self._dir_children[parent] = names
        return names

    def _snap_to_existing_dirs(self, rel: str, cutoff: float = 0.8) -> str:
        parts = [p for p in rel.strip("/").split("/") if p]
        if not parts:
            return rel
        # enforce root
        if parts[0].lower() != self.root_name.lower():
            parts = [self.root_name] + parts
        cur = self.folder
        snapped: List[str] = [self.root_name]
        for seg in parts[1:]:
            children = self._iter_children(cur)
            match = difflib.get_close_matches(seg, children, n=1, cutoff=cutoff)
            chosen = match[0] if match else seg
            snapped.append(chosen)
            cur = cur / chosen
        return "/".join(snapped)


if __name__ == "__main__":
    app = OrganizerApp()
    app.mainloop()

