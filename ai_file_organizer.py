import os
import re
import json
import csv
import time
import shutil
import threading
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---- AI backends with enhanced context awareness -------------------------
from ai_backends import (
    query_ollama,
    query_openai,
    query_grok,
    list_ollama_models,
    test_ai_connection,
    analyze_folder_structure,
    build_context_prompt,
    extract_clean_path,
    validate_folder_path,
)

AI_BACKENDS = ["Local (Ollama)", "OpenAI", "Grok"]

HISTORY_FILE = "organizer_history.json"
RULES_FILE   = "organizer_rules.json"
DEFAULT_MAX_WORKERS = max(4, os.cpu_count() or 4)

# Terraform guardrail default folder under project root
TERRAFORM_SUBPATH = Path("infrastructure/terraform")

# Project markers
PROJECT_MARKERS = {".git", "package.json", "go.mod", "pyproject.toml", "main.tf"}
TF_EXTS = {".tf", ".tfvars", ".tfstate", ".lock.hcl"}


class OrganizerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("AI File Organizer - Enhanced")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        # Runtime state
        self.scanning = False
        self.cancel_event = threading.Event()
        self.current_futures = set()
        self.executor = ThreadPoolExecutor(max_workers=DEFAULT_MAX_WORKERS)

        self.folder: Optional[Path] = None
        self.root_name: str = ""
        self.is_project: bool = False
        self.has_terraform: bool = False
        self.folder_structure: Dict = {}  # New: store analyzed folder structure

        self.file_items: List[Tuple[Path, str, tk.BooleanVar, str]] = []  # (src, ai_target, checked, status)
        self.model_list: List[str] = []
        self.history: Dict[str, dict] = {}
        self.rules: Dict[str, str] = {}

        self._load_history()
        self._load_rules()

        # UI vars
        self.selected_backend = tk.StringVar(value=AI_BACKENDS[0])
        self.selected_model   = tk.StringVar(value="")
        self.api_key          = tk.StringVar(value="")
        self.status_var       = tk.StringVar(value="Select a folder to start.")
        self.progress_var     = tk.IntVar(value=0)
        self.select_all_var   = tk.BooleanVar(value=False)

        # Enhanced options
        self.analyze_structure_var  = tk.BooleanVar(value=True)   # New: analyze existing structure
        self.use_context_var        = tk.BooleanVar(value=True)   # New: use contextual prompts
        
        # Guardrails
        self.stay_under_root_var    = tk.BooleanVar(value=True)
        self.pin_terraform_var      = tk.BooleanVar(value=True)
        self.prefer_folder_move_var = tk.BooleanVar(value=True)

        # Scan options
        self.ignore_cache_this_run  = False      # for Rescan (fresh AI)
        self.refine_two_pass_var    = tk.BooleanVar(value=True)

        # Temp scan log (JSONL) + lock
        self.tmp_scan_path: Optional[Path] = None
        self.tmp_lock = threading.Lock()

        # UI
        self._build_ui()
        self._on_backend_change()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------------------------------------------------------------- UI -----
    def _build_ui(self):
        # Top bar
        top = ttk.Frame(self); top.pack(side=tk.TOP, fill=tk.X, padx=12, pady=8)

        ttk.Button(top, text="Select Folder", command=self._on_choose_folder).pack(side=tk.LEFT, padx=(0,8))
        self.folder_lbl = ttk.Label(top, text="(none)")
        self.folder_lbl.pack(side=tk.LEFT, padx=(0,12))

        ttk.Button(top, text="Analyze Structure", command=self._on_analyze_structure).pack(side=tk.LEFT, padx=(0,8))
        ttk.Button(top, text="Scan with AI", command=self._on_scan).pack(side=tk.LEFT, padx=(0,8))
        ttk.Button(top, text="Rescan (fresh AI)", command=self._on_rescan_fresh).pack(side=tk.LEFT, padx=(0,8))
        ttk.Button(top, text="Clear cache", command=self._on_clear_cache).pack(side=tk.LEFT, padx=(0,8))
        ttk.Button(top, text="Cancel Scan", command=self._on_cancel_scan).pack(side=tk.LEFT, padx=(0,8))

        # Connection / settings - First row
        cfg1 = ttk.Frame(self); cfg1.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(0,3))

        ttk.Label(cfg1, text="Backend:").pack(side=tk.LEFT)
        self.backend_cb = ttk.Combobox(cfg1, textvariable=self.selected_backend, values=AI_BACKENDS, width=16, state="readonly")
        self.backend_cb.bind("<<ComboboxSelected>>", lambda e: self._on_backend_change())
        self.backend_cb.pack(side=tk.LEFT, padx=(6,12))

        ttk.Label(cfg1, text="Model:").pack(side=tk.LEFT)
        self.model_cb = ttk.Combobox(cfg1, textvariable=self.selected_model, values=self.model_list, width=22)
        self.model_cb.pack(side=tk.LEFT, padx=(6,12))

        ttk.Label(cfg1, text="API Key:").pack(side=tk.LEFT)
        self.api_entry = ttk.Entry(cfg1, textvariable=self.api_key, show="•", width=30)
        self.api_entry.pack(side=tk.LEFT, padx=(6,6))
        ttk.Button(cfg1, text="Test", command=self._on_test_ai).pack(side=tk.LEFT, padx=(2,12))

        # Enhanced options - Second row
        cfg2 = ttk.Frame(self); cfg2.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(0,6))
        
        ttk.Checkbutton(cfg2, text="Analyze existing structure", variable=self.analyze_structure_var).pack(side=tk.LEFT, padx=(0,12))
        ttk.Checkbutton(cfg2, text="Use contextual AI prompts", variable=self.use_context_var).pack(side=tk.LEFT, padx=(0,12))
        ttk.Checkbutton(cfg2, text="Refine suggestions (two‑pass)", variable=self.refine_two_pass_var).pack(side=tk.LEFT, padx=(0,12))
        ttk.Checkbutton(cfg2, text="Select All", variable=self.select_all_var, command=self._on_select_all).pack(side=tk.LEFT, padx=(0,12))

        # Guardrails - Third row
        cfg3 = ttk.Frame(self); cfg3.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(0,6))
        
        ttk.Checkbutton(cfg3, text="Stay under root", variable=self.stay_under_root_var).pack(side=tk.LEFT, padx=(0,10))
        ttk.Checkbutton(cfg3, text="Pin Terraform", variable=self.pin_terraform_var).pack(side=tk.LEFT, padx=(0,10))
        ttk.Checkbutton(cfg3, text="Prefer folder move", variable=self.prefer_folder_move_var).pack(side=tk.LEFT, padx=(0,10))

        # Structure info display
        self.structure_info = ttk.Label(self, text="", foreground="blue", font=("TkDefaultFont", 8))
        self.structure_info.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(0,6))

        # Tree
        tree_frame = ttk.Frame(self); tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=6)
        columns = ("Select", "Source Path", "Target Path", "Status", "Confidence")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("Select", text="✓")
        self.tree.heading("Source Path", text="Source Path")
        self.tree.heading("Target Path", text="AI Suggested Path")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Confidence", text="AI Confidence")
        self.tree.column("Select", width=50, anchor=tk.CENTER, stretch=False)
        self.tree.column("Source Path", width=500, anchor=tk.W, stretch=True)
        self.tree.column("Target Path", width=500, anchor=tk.W, stretch=True)
        self.tree.column("Status", width=150, anchor=tk.W, stretch=False)
        self.tree.column("Confidence", width=100, anchor=tk.CENTER, stretch=False)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=y_scroll.set)

        x_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(xscrollcommand=x_scroll.set)

        # Bottom actions
        act = ttk.Frame(self); act.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=8)
        self.progress = ttk.Progressbar(act, orient=tk.HORIZONTAL, mode="determinate", maximum=100, variable=self.progress_var)
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,8))
        ttk.Label(act, textvariable=self.status_var).pack(side=tk.LEFT)

        exp = ttk.Frame(self); exp.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0,8))
        ttk.Button(exp, text="Export List", command=self._on_export_list).pack(side=tk.LEFT)
        ttk.Button(exp, text="Show Structure Analysis", command=self._on_show_structure).pack(side=tk.LEFT, padx=(8,0))
        ttk.Button(exp, text="Organize", command=self._on_organize).pack(side=tk.LEFT, padx=(8,0))

    # ------------------------------------------------------------ Events -----
    def _on_choose_folder(self):
        folder = filedialog.askdirectory(title="Choose a folder to scan")
        if not folder:
            return
        self.folder = Path(folder)
        self.root_name = self.folder.name
        self.folder_lbl.configure(text=str(self.folder))
        self.status_var.set("Ready. Click 'Analyze Structure' to understand the folder organization.")
        self.is_project, self.has_terraform = self._detect_project(self.folder)
        self.folder_structure = {}  # Reset structure analysis
        self._clear_tree()
        self._update_structure_info()

    def _on_analyze_structure(self):
        """Analyze the existing folder structure"""
        if not self.folder:
            messagebox.showwarning("No folder", "Please choose a folder first.")
            return
        
        self.status_var.set("Analyzing folder structure...")
        self.folder_structure = analyze_folder_structure(self.folder)
        self._update_structure_info()
        self.status_var.set("Structure analysis complete. Ready to scan with AI.")

    def _on_show_structure(self):
        """Show detailed structure analysis"""
        if not self.folder_structure:
            messagebox.showinfo("No Analysis", "Please analyze the folder structure first.")
            return
        
        # Create a popup window with structure details
        popup = tk.Toplevel(self)
        popup.title("Folder Structure Analysis")
        popup.geometry("600x400")
        
        text_widget = tk.Text(popup, wrap=tk.WORD, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Format structure information
        info_text = f"Analysis of: {self.folder}\n\n"
        info_text += f"Existing folders: {len(self.folder_structure.get('existing_folders', []))}\n"
        info_text += f"Max depth: {self.folder_structure.get('depth_info', {}).get('max_depth', 0)}\n\n"
        
        if self.folder_structure.get('existing_folders'):
            info_text += "Existing folders:\n"
            for folder in sorted(self.folder_structure['existing_folders']):
                info_text += f"  • {folder}\n"
            info_text += "\n"
        
        if self.folder_structure.get('folder_patterns'):
            info_text += "Detected patterns:\n"
            for category, folders in self.folder_structure['folder_patterns'].items():
                info_text += f"  {category}: {', '.join(folders)}\n"
            info_text += "\n"
        
        if self.folder_structure.get('common_extensions'):
            info_text += "Common file types:\n"
            for ext in sorted(self.folder_structure['common_extensions']):
                info_text += f"  {ext}\n"
        
        text_widget.insert(tk.END, info_text)
        text_widget.configure(state="disabled")
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _update_structure_info(self):
        """Update the structure info display"""
        if not self.folder_structure:
            self.structure_info.configure(text="")
            return
        
        folders_count = len(self.folder_structure.get('existing_folders', []))
        patterns_count = len(self.folder_structure.get('folder_patterns', {}))
        max_depth = self.folder_structure.get('depth_info', {}).get('max_depth', 0)
        
        info_text = f"Structure: {folders_count} existing folders, {patterns_count} patterns detected, max depth: {max_depth}"
        self.structure_info.configure(text=info_text)

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
        ok, msg = test_ai_connection(self.selected_backend.get(),
                                     self.selected_model.get().strip(),
                                     self.api_key.get().strip())
        if ok:  messagebox.showinfo("AI Connection", msg or "OK")
        else:   messagebox.showerror("AI Connection", msg or "Failed")

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

        # Auto-analyze structure if not done and enabled
        if self.analyze_structure_var.get() and not self.folder_structure:
            self.status_var.set("Auto-analyzing folder structure...")
            self.folder_structure = analyze_folder_structure(self.folder)
            self._update_structure_info()

        # per-run temp JSONL log
        try:
            tmpdir = Path(tempfile.gettempdir())
            self.tmp_scan_path = tmpdir / f"ai_scan_{int(time.time())}.jsonl"
        except Exception:
            self.tmp_scan_path = None

        self.scanning = True
        self.cancel_event.clear()
        self.current_futures.clear()

        self.progress_var.set(0)
        self.status_var.set("Scanning with enhanced AI...")
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
        for (_,_,checked,_) in self.file_items:
            checked.set(v)

    def _on_organize(self):
        sel = [(s,t,c,st) for (s,t,c,st) in self.file_items if c.get()]
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
        path = filedialog.asksaveasfilename(
            title="Export list to CSV",
            defaultextension=".csv",
            filetypes=[("CSV","*.csv"), ("All Files","*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["checked","source","target","status","confidence"])
                for (src, tgt, chk, st) in self.file_items:
                    # Extract confidence from status if available
                    confidence = "N/A"
                    if "confidence:" in st.lower():
                        try:
                            confidence = st.split("confidence:")[-1].strip()
                        except:
                            pass
                    w.writerow([bool(chk.get()), str(src), tgt, st, confidence])
            messagebox.showinfo("Exported", f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Export error", str(e))

    # ------------------------------------------------------- Scan / AI -------
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
            model   = self.selected_model.get().strip()
            api_key = self.api_key.get().strip()
            refine  = self.refine_two_pass_var.get()

            future_to_file: Dict = {}
            for f in files:
                if not self.scanning or self.cancel_event.is_set():
                    break
                fut = self.executor.submit(
                    self._process_file_enhanced, f, backend, model, api_key,
                    self.ignore_cache_this_run, refine
                )
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
                self.after(0, lambda c=completed,t=total: self.status_var.set(f"Enhanced scanning... {c}/{t}"))

            for fut in future_to_file:
                if not fut.done():
                    fut.cancel()
            self.current_futures.difference_update(future_to_file.keys())
        finally:
            self.after(0, self._finish_scan)

    def _finish_scan(self):
        self.scanning = False
        self.progress_var.set(0)
        self.status_var.set("Scan cancelled." if self.cancel_event.is_set() else "Enhanced scan complete.")
        self.ignore_cache_this_run = False

    # ------------------------------ Enhanced AI processing (per file) --------
    def _process_file_enhanced(self, file_path: Path, backend: str, model: str, api_key: str,
                              ignore_cache: bool, refine: bool) -> Tuple[str, str]:
        """Enhanced file processing with contextual AI prompts"""
        if self.cancel_event.is_set():
            return "Uncategorized", "Cancelled"

        sig = self._signature(file_path)
        hint = self._build_file_hint(file_path)

        # Pass 1 (cache or fresh with enhanced context)
        if not ignore_cache and sig in self.history:
            first_path = self.history[sig].get("ai_path", "Uncategorized")
            first_src  = "Cached"
            confidence = self.history[sig].get("confidence", "N/A")
        else:
            # Use contextual prompts if enabled and structure is available
            if self.use_context_var.get() and self.folder_structure:
                context_prompt = build_context_prompt(file_path, hint, self.folder_structure, self.root_name)
                first_raw = self._query_ai_path_enhanced(context_prompt, backend, model, api_key)
                confidence = self._estimate_confidence(first_raw, file_path)
            else:
                # Fallback to basic prompt
                basic_prompt = (
                    f"Organize this file into a folder path (1-3 levels max):\n"
                    f"File: {file_path.name}\n"
                    f"Info: {hint}\n"
                    f"Root: {self.root_name}\n\n"
                    f"Return only the folder path (e.g., 'Documents/Reports'):"
                )
                first_raw = self._query_ai_path_enhanced(basic_prompt, backend, model, api_key)
                confidence = "Basic"
            
            first_path = self._apply_guardrails(file_path, extract_clean_path(first_raw))
            first_src  = f"AI suggested (confidence: {confidence})"

        self._append_temp_log({
            "ts": time.time(), "source": str(file_path), "hint": hint,
            "first_path": first_path, "refined_path": None, "status": first_src,
            "confidence": confidence if 'confidence' in locals() else "N/A"
        })

        if self.cancel_event.is_set():
            return "Uncategorized", "Cancelled"

        # Pass 2 (refinement with context)
        if refine and not first_src.startswith("Cached"):
            refined_raw = self._refine_ai_path_enhanced(file_path, hint, first_path, backend, model, api_key)
            refined_path = self._apply_guardrails(file_path, extract_clean_path(refined_raw))
            final_path = refined_path if refined_path != first_path else first_path
            status = f"{first_src} → Refined"
        else:
            final_path = first_path
            status = first_src

        # Save enhanced info to history
        self.history[sig] = {
            "ai_path": final_path, 
            "fullpath": str(file_path), 
            "timestamp": time.time(),
            "confidence": confidence if 'confidence' in locals() else "N/A",
            "context_used": self.use_context_var.get()
        }
        self._save_history()

        return final_path, status

    def _query_ai_path_enhanced(self, prompt: str, backend: str, model: str, api_key: str) -> str:
        """Enhanced AI query with better error handling"""
        if self.cancel_event.is_set():
            return "Uncategorized"

        try:
            if backend == "Local (Ollama)":
                text = query_ollama(model=model or "llama3.1", prompt=prompt)
            elif backend == "OpenAI":
                text = query_openai(api_key=api_key, model=model or "gpt-4o-mini", prompt=prompt)
            elif backend == "Grok":
                text = query_grok(api_key=api_key, model=model or "grok-2-mini", prompt=prompt)
            else:
                text = "Uncategorized"
        except Exception as e:
            text = f"Error: {e}"
        
        return text

    def _refine_ai_path_enhanced(self, file_path: Path, hint: str, first_path: str,
                                backend: str, model: str, api_key: str) -> str:
        """Enhanced refinement with context awareness"""
        if self.cancel_event.is_set():
            return first_path

        # Build refinement prompt with context
        refinement_prompt = f"""Review and improve this file organization suggestion:

File: {file_path.name}
Info: {hint}
Current suggestion: {first_path}
Root folder: {self.root_name}"""

        if self.folder_structure.get('existing_folders'):
            existing = list(self.folder_structure['existing_folders'])[:15]  # Limit context
            refinement_prompt += f"\nExisting folders: {', '.join(existing)}"

        refinement_prompt += """\n\nImprove the path if needed, considering:
1. Existing folder structure
2. File type and content
3. Logical organization
4. Consistency with similar files

Return ONLY the improved folder path or the original if it's already good:"""

        try:
            if backend == "Local (Ollama)":
                text = query_ollama(model=model or "llama3.1", prompt=refinement_prompt)
            elif backend == "OpenAI":
                text = query_openai(api_key=api_key, model=model or "gpt-4o-mini", prompt=refinement_prompt)
            elif backend == "Grok":
                text = query_grok(api_key=api_key, model=model or "grok-2-mini", prompt=refinement_prompt)
            else:
                text = first_path
        except Exception:
            text = first_path

        refined = extract_clean_path(text)
        if not refined or refined.lower() == "uncategorized":
            return first_path
        if refined.strip().lower() == first_path.strip().lower():
            return first_path
        return refined

    def _estimate_confidence(self, ai_response: str, file_path: Path) -> str:
        """Estimate confidence based on AI response characteristics"""
        if not ai_response or ai_response.startswith("Error"):
            return "Low"
        
        # Simple heuristics for confidence estimation
        response_length = len(ai_response.strip())
        has_clear_path = "/" in ai_response or any(word in ai_response.lower() 
                                                  for word in ["documents", "images", "media", "code", "data"])
        
        if response_length > 50 and has_clear_path:
            return "High"
        elif response_length > 20:
            return "Medium"
        else:
            return "Low"

    # ---------------------- Enhanced Guardrails -----------------------------
    def _apply_guardrails(self, file_path: Path, ai_path: str) -> str:
        """Enhanced guardrails with better path validation"""
        rel = validate_folder_path(ai_path)

        # Terraform pinning
        if self.pin_terraform_var.get() and (file_path.suffix.lower() in TF_EXTS or file_path.name.endswith(".lock.hcl")):
            pinned = Path(self.root_name) / TERRAFORM_SUBPATH
            return str(pinned)

        # Stay under root
        if self.stay_under_root_var.get():
            if not self._starts_with_root(rel):
                rel = str(Path(self.root_name) / rel)

        return rel

    def _starts_with_root(self, rel: str) -> bool:
        parts = [p for p in str(rel).strip("/").split("/") if p]
        return (len(parts) > 0) and (parts[0].lower() == self.root_name.lower())

    # Enhanced file hint with more context
    def _build_file_hint(self, p: Path) -> str:
        ext = p.suffix.lower()
        parent = p.parent.name
        name = p.name
        
        # Get file size
        try:
            size = p.stat().st_size
            size_desc = self._format_size(size)
        except Exception:
            size = 0
            size_desc = "unknown size"

        # Enhanced type detection
        if ext in {".jpg",".jpeg",".png",".heic",".webp",".tif",".tiff",".gif",".bmp"}:
            return f"Type=Image; Size={size_desc}; Name={name}; Parent={parent}; Extension={ext}"
        elif ext in {".mp3",".m4a",".flac",".wav",".aac",".ogg",".wma"}:
            return f"Type=Audio; Size={size_desc}; Name={name}; Parent={parent}; Extension={ext}"
        elif ext in {".mp4",".mov",".mkv",".avi",".webm",".wmv",".flv"}:
            return f"Type=Video; Size={size_desc}; Name={name}; Parent={parent}; Extension={ext}"
        elif ext in {".pdf",".doc",".docx",".ppt",".pptx",".xls",".xlsx",".md",".txt",".rtf"}:
            return f"Type=Document; Size={size_desc}; Name={name}; Parent={parent}; Extension={ext}"
        elif ext in {".py",".js",".html",".css",".java",".cpp",".c",".php",".rb",".go"}:
            return f"Type=Code; Size={size_desc}; Name={name}; Parent={parent}; Language={ext[1:]}"
        elif ext in {".zip",".rar",".7z",".tar",".gz",".bz2"}:
            return f"Type=Archive; Size={size_desc}; Name={name}; Parent={parent}; Format={ext[1:]}"
        elif ext in TF_EXTS or p.name.endswith(".lock.hcl"):
            return f"Type=Terraform; Size={size_desc}; Name={name}; Parent={parent}"
        else:
            return f"Type=Unknown; Size={size_desc}; Name={name}; Parent={parent}; Extension={ext or '(none)'}"

    def _format_size(self, size: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}TB"

    # ---------------------------------------------- Organize (enhanced) -----
    def _organize_files_async(self, selected_files, dest_path: Path):
        def top_app_bundle(p: Path) -> Optional[Path]:
            for anc in (p,) + tuple(p.parents):
                if anc.suffix.lower() == ".app":
                    return anc
            return None

        def maj_prefix(paths: List[str], k: int = 2) -> Tuple[str, ...]:
            cleaned = [tuple(Path(p).parts[:k]) for p in paths if p]
            if not cleaned: return ()
            return Counter(cleaned).most_common(1)[0][0]

        def organize():
            success = errors = 0
            groups: Dict[Path, List[Tuple[Path, str]]] = defaultdict(list)
            for src, tgt, chk, _ in selected_files:
                if not chk.get(): continue
                root = top_app_bundle(src) or src.parent
                groups[root].append((src, tgt))

            folder_moves: Dict[Path, Path] = {}
            for src_dir, items in groups.items():
                tgts = [t for _,t in items]
                counts = Counter(tuple(Path(t).parts[:2]) for t in tgts if t)
                agree = (counts.most_common(1)[0][1]/len(tgts)) if tgts else 0.0

                # prefer folder move for projects or .app, or majority agreement
                if (self.prefer_folder_move_var.get() and self.is_project) or src_dir.suffix.lower() == ".app" or (len(items)>4 and agree>=0.6):
                    base = Path(*maj_prefix(tgts,k=2)) if tgts else Path(self.root_name if self.stay_under_root_var.get() else "Uncategorized")
                    if self.stay_under_root_var.get():
                        if not (len(base.parts) > 0 and base.parts[0].lower() == self.root_name.lower()):
                            base = Path(self.root_name) / base
                    folder_moves[src_dir] = dest_path / base / src_dir.name

            # Move folders first
            for src_dir, dst_dir in folder_moves.items():
                try:
                    dst_dir.parent.mkdir(parents=True, exist_ok=True)
                    candidate = dst_dir; i=1
                    while candidate.exists():
                        candidate = dst_dir.with_name(f"{dst_dir.name}_{i}"); i+=1
                    shutil.move(str(src_dir), str(candidate))
                    success += 1
                except Exception as e:
                    print(f"Error moving folder {src_dir}: {e}"); errors += 1

            moved_roots = set(folder_moves.keys())
            remaining = [(s,t) for (s,t,c,_) in selected_files if c.get()
                         and not any(s==r or r in s.parents for r in moved_roots)]

            total = max(1, len(remaining))
            for i,(src,tgt) in enumerate(remaining):
                try:
                    tpath = Path(tgt)
                    if self.stay_under_root_var.get():
                        if not (len(tpath.parts)>0 and tpath.parts[0].lower()==self.root_name.lower()):
                            tpath = Path(self.root_name) / tpath

                    tdir = dest_path / tpath
                    tdir.mkdir(parents=True, exist_ok=True)
                    target = tdir / src.name
                    n=1
                    while target.exists():
                        target = tdir / f"{src.stem}_{n}{src.suffix}"; n+=1
                    shutil.move(str(src), str(target))
                    success += 1
                except Exception as e:
                    print(f"Error organizing {src}: {e}"); errors += 1

                prog = int((i+1)*100/total)
                self.after(0, lambda p=prog: self.progress_var.set(p))
                self.after(0, lambda s=success,e=errors: self.status_var.set(f'Organizing... Success: {s}, Errors: {e}'))

            self.after(0, lambda: self.progress_var.set(0))
            self.after(0, lambda: self.status_var.set(f"Organization complete! Success: {success}, Errors: {errors}"))
            if errors==0:
                self.after(0, lambda: messagebox.showinfo("Success", f"All {success} item(s) organized!"))
            else:
                self.after(0, lambda: messagebox.showwarning("Completed with Errors",
                                                             f"Organized {success} item(s), {errors} failed."))
        threading.Thread(target=organize, daemon=True).start()

    # ------------------------------------------------------------- Temp Log ---
    def _append_temp_log(self, obj: dict):
        """Append a JSON line to the temp scan file (thread-safe)."""
        if not self.tmp_scan_path:
            return
        line = json.dumps(obj, ensure_ascii=False)
        with self.tmp_lock:
            try:
                with open(self.tmp_scan_path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception:
                pass

    # ------------------------------------------------------------- Tree UI ---
    def _add_file_to_tree(self, entry: Tuple[Path, str, tk.BooleanVar, str]):
        src, ai_path, checked, status = entry
        checkbox = "☑" if checked.get() else "☐"
        
        # Extract confidence for display
        confidence = "N/A"
        if "confidence:" in status.lower():
            try:
                confidence = status.split("confidence:")[-1].split(")")[0].strip()
            except:
                pass
        
        iid = self.tree.insert("", "end",
                               values=(checkbox, str(src), ai_path, status, confidence))
        try:
            self.tree.see(iid)
            self.tree.yview_moveto(1.0)
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

    # ------------------------------------------------------- Helpers/State ---
    def _signature(self, p: Path) -> str:
        try:
            st = p.stat()
            return f"{p.name}|{st.st_size}|{int(st.st_mtime)}"
        except Exception:
            return f"{p.name}|0|0"

    def _detect_project(self, root: Path) -> Tuple[bool, bool]:
        """Detect if folder is a 'project' and whether it has Terraform."""
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
            with open(HISTORY_FILE,"r",encoding="utf-8") as f:
                self.history = json.load(f)
        except Exception:
            self.history = {}

    def _save_history(self):
        try:
            with open(HISTORY_FILE,"w",encoding="utf-8") as f:
                json.dump(self.history, f)
        except Exception:
            pass

    def _load_rules(self):
        try:
            with open(RULES_FILE,"r",encoding="utf-8") as f:
                self.rules = json.load(f)
        except Exception:
            self.rules = {}

    # ---------------------------------------------------------------- Close ---
    def _on_close(self):
        try: self._on_cancel_scan()
        except Exception: pass
        try:
            self.executor.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            try: self.executor.shutdown(wait=False)
            except Exception: pass
        self.destroy()


if __name__ == "__main__":
    app = OrganizerApp()
    app.mainloop()