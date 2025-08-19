#!/usr/bin/env python3
"""
Enhanced AI File Organizer with Context-Aware Path Suggestions

This improved version addresses the limitations of the original:
1. Better AI path suggestions considering file context and existing structure
2. Path-aware organization using current file location
3. Enhanced prompt engineering for more accurate results
4. Improved file analysis with better context extraction
5. Smarter folder structure suggestions based on project type
"""

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
from typing import Optional, Tuple, List, Dict, Set
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

# AI backends
from ai_backends import (
    query_ollama,
    query_openai,
    query_grok,
    list_ollama_models,
    test_ai_connection,
    optimize_prompt_for_backend,
    validate_folder_path
)

AI_BACKENDS = ["Local (Ollama)", "OpenAI", "Grok"]

HISTORY_FILE = "ai_organizer_history.json"
RULES_FILE = "ai_organizer_rules.json"
DEFAULT_MAX_WORKERS = max(4, os.cpu_count() or 4)

# Enhanced project detection
PROJECT_MARKERS = {
    ".git", "package.json", "go.mod", "pyproject.toml", "main.tf", 
    "Cargo.toml", "requirements.txt", "setup.py", "pom.xml", "build.gradle",
    "Makefile", "CMakeLists.txt", "Dockerfile", "docker-compose.yml",
    "README.md", "LICENSE", ".gitignore"
}

# File type categories with better context
FILE_CATEGORIES = {
    "code": {".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".hpp", ".cs", ".php", ".rb", ".go", ".rs", ".swift", ".kt"},
    "config": {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env", ".properties"},
    "docs": {".md", ".txt", ".rst", ".adoc", ".tex", ".doc", ".docx", ".pdf", ".rtf"},
    "images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg", ".ico"},
    "audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"},
    "video": {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v"},
    "archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "data": {".csv", ".xlsx", ".xls", ".db", ".sqlite", ".xml", ".json"},
    "terraform": {".tf", ".tfvars", ".tfstate", ".lock.hcl"},
    "docker": {"Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"},
    "git": {".gitignore", ".gitattributes", ".gitmodules"},
    "logs": {".log", ".out", ".err", ".trace"}
}

class EnhancedFileAnalyzer:
    """Enhanced file analysis with context awareness"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.project_structure = self._analyze_project_structure()
        self.folder_patterns = self._extract_folder_patterns()
        
    def _analyze_project_structure(self) -> Dict[str, Set[str]]:
        """Analyze existing folder structure to understand organization patterns"""
        structure = defaultdict(set)
        
        try:
            for root, dirs, files in os.walk(self.root_path):
                rel_path = Path(root).relative_to(self.root_path)
                if rel_path == Path('.'):
                    continue
                    
                # Analyze folder names for patterns
                folder_name = rel_path.name.lower()
                
                # Detect common patterns
                if any(pattern in folder_name for pattern in ['src', 'source', 'lib', 'app']):
                    structure['code_folders'].add(str(rel_path))
                elif any(pattern in folder_name for pattern in ['doc', 'docs', 'readme', 'manual']):
                    structure['doc_folders'].add(str(rel_path))
                elif any(pattern in folder_name for pattern in ['test', 'tests', 'spec', 'unit']):
                    structure['test_folders'].add(str(rel_path))
                elif any(pattern in folder_name for pattern in ['config', 'conf', 'settings']):
                    structure['config_folders'].add(str(rel_path))
                elif any(pattern in folder_name for pattern in ['assets', 'images', 'media', 'static']):
                    structure['asset_folders'].add(str(rel_path))
                    
        except Exception:
            pass
            
        return dict(structure)
    
    def _extract_folder_patterns(self) -> Dict[str, List[str]]:
        """Extract common folder naming patterns"""
        patterns = defaultdict(list)
        
        try:
            for root, dirs, _ in os.walk(self.root_path):
                for dir_name in dirs:
                    # Analyze folder naming conventions
                    if re.match(r'^[a-z]+[a-z0-9-]*$', dir_name):
                        patterns['kebab_case'].append(dir_name)
                    elif re.match(r'^[A-Z][a-zA-Z0-9]*$', dir_name):
                        patterns['pascal_case'].append(dir_name)
                    elif re.match(r'^[a-z][a-z0-9_]*$', dir_name):
                        patterns['snake_case'].append(dir_name)
                        
        except Exception:
            pass
            
        return dict(patterns)
    
    def get_file_context(self, file_path: Path) -> Dict[str, str]:
        """Get comprehensive context for a file"""
        rel_path = file_path.relative_to(self.root_path)
        parent_dir = rel_path.parent
        file_name = file_path.name
        file_ext = file_path.suffix.lower()
        
        context = {
            'filename': file_name,
            'extension': file_ext,
            'parent_dir': str(parent_dir),
            'relative_path': str(rel_path),
            'depth': len(rel_path.parts),
            'file_category': self._categorize_file(file_path),
            'project_type': self._detect_project_type(),
            'sibling_files': self._get_sibling_files(file_path),
            'folder_pattern': self._get_folder_pattern(),
            'existing_structure': self._get_relevant_structure(parent_dir)
        }
        
        return context
    
    def _categorize_file(self, file_path: Path) -> str:
        """Enhanced file categorization"""
        file_ext = file_path.suffix.lower()
        file_name = file_path.name.lower()
        
        # Check specific file types first
        for category, extensions in FILE_CATEGORIES.items():
            if file_ext in extensions or file_name in extensions:
                return category
        
        # Check file content hints
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                if first_line.startswith('#!'):
                    return 'scripts'
                elif first_line.startswith('<?xml'):
                    return 'xml'
                elif first_line.startswith('{') or first_line.startswith('['):
                    return 'json'
        except Exception:
            pass
        
        return 'unknown'
    
    def _detect_project_type(self) -> str:
        """Detect the type of project based on root directory contents"""
        try:
            root_files = set(os.listdir(self.root_path))
            
            if '.git' in root_files:
                if 'package.json' in root_files:
                    return 'nodejs'
                elif 'pyproject.toml' in root_files or 'requirements.txt' in root_files:
                    return 'python'
                elif 'go.mod' in root_files:
                    return 'golang'
                elif 'Cargo.toml' in root_files:
                    return 'rust'
                elif 'pom.xml' in root_files:
                    return 'java_maven'
                elif 'build.gradle' in root_files:
                    return 'java_gradle'
                elif any(f.endswith('.tf') for f in root_files):
                    return 'terraform'
                else:
                    return 'git_repo'
            elif 'Dockerfile' in root_files:
                return 'docker'
            elif any(f.endswith('.tf') for f in root_files):
                return 'terraform'
            else:
                return 'general'
                
        except Exception:
            return 'unknown'
    
    def _get_sibling_files(self, file_path: Path) -> List[str]:
        """Get list of sibling files for context"""
        try:
            parent = file_path.parent
            siblings = [f.name for f in parent.iterdir() if f.is_file() and f != file_path]
            return siblings[:10]  # Limit to first 10
        except Exception:
            return []
    
    def _get_folder_pattern(self) -> str:
        """Get the dominant folder naming pattern"""
        if not self.folder_patterns:
            return 'unknown'
        
        # Find the most common pattern
        max_count = 0
        dominant_pattern = 'unknown'
        
        for pattern, folders in self.folder_patterns.items():
            if len(folders) > max_count:
                max_count = len(folders)
                dominant_pattern = pattern
                
        return dominant_pattern
    
    def _get_relevant_structure(self, parent_dir: Path) -> Dict[str, str]:
        """Get relevant existing folder structure"""
        relevant = {}
        
        for category, folders in self.project_structure.items():
            for folder in folders:
                folder_path = Path(folder)
                if folder_path == parent_dir or folder_path in parent_dir.parents:
                    relevant[category] = folder
                    break
                    
        return relevant


class EnhancedAIOrganizer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Enhanced AI File Organizer")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        # Runtime state
        self.scanning = False
        self.cancel_event = threading.Event()
        self.current_futures = set()
        self.executor = ThreadPoolExecutor(max_workers=DEFAULT_MAX_WORKERS)

        self.folder: Optional[Path] = None
        self.root_name: str = ""
        self.analyzer: Optional[EnhancedFileAnalyzer] = None

        self.file_items: List[Tuple[Path, str, tk.BooleanVar, str]] = []
        self.model_list: List[str] = []
        self.history: Dict[str, dict] = {}
        self.rules: Dict[str, str] = {}

        self._load_history()
        self._load_rules()

        # UI vars
        self.selected_backend = tk.StringVar(value=AI_BACKENDS[0])
        self.selected_model = tk.StringVar(value="")
        self.api_key = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Select a folder to start.")
        self.progress_var = tk.IntVar(value=0)
        self.select_all_var = tk.BooleanVar(value=False)

        # Enhanced options
        self.use_context_var = tk.BooleanVar(value=True)
        self.consider_structure_var = tk.BooleanVar(value=True)
        self.smart_grouping_var = tk.BooleanVar(value=True)
        self.refine_suggestions_var = tk.BooleanVar(value=True)

        # Scan options
        self.ignore_cache_this_run = False
        self.tmp_scan_path: Optional[Path] = None
        self.tmp_lock = threading.Lock()

        # UI
        self._build_ui()
        self._on_backend_change()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Top bar
        top = ttk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, padx=12, pady=8)

        ttk.Button(top, text="Select Folder", command=self._on_choose_folder).pack(side=tk.LEFT, padx=(0,8))
        self.folder_lbl = ttk.Label(top, text="(none)")
        self.folder_lbl.pack(side=tk.LEFT, padx=(0,12))

        ttk.Button(top, text="Scan with AI", command=self._on_scan).pack(side=tk.LEFT, padx=(0,8))
        ttk.Button(top, text="Rescan (fresh AI)", command=self._on_rescan_fresh).pack(side=tk.LEFT, padx=(0,8))
        ttk.Button(top, text="Clear Cache", command=self._on_clear_cache).pack(side=tk.LEFT, padx=(0,8))
        ttk.Button(top, text="Cancel Scan", command=self._on_cancel_scan).pack(side=tk.LEFT, padx=(0,8))

        # Connection / settings
        cfg = ttk.Frame(self)
        cfg.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(0,6))

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

        # Enhanced options
        ttk.Checkbutton(cfg, text="Use Context", variable=self.use_context_var).pack(side=tk.LEFT, padx=(0,8))
        ttk.Checkbutton(cfg, text="Consider Structure", variable=self.consider_structure_var).pack(side=tk.LEFT, padx=(0,8))
        ttk.Checkbutton(cfg, text="Smart Grouping", variable=self.smart_grouping_var).pack(side=tk.LEFT, padx=(0,8))
        ttk.Checkbutton(cfg, text="Refine Suggestions", variable=self.refine_suggestions_var).pack(side=tk.LEFT, padx=(0,8))
        ttk.Checkbutton(cfg, text="Select All", variable=self.select_all_var, command=self._on_select_all).pack(side=tk.LEFT, padx=(0,8))

        # Tree
        tree_frame = ttk.Frame(self)
        tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=6)
        
        columns = ("Select", "Source Path", "Target Path", "Context", "Status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("Select", text="✓")
        self.tree.heading("Source Path", text="Source Path")
        self.tree.heading("Target Path", text="AI Suggested Path")
        self.tree.heading("Context", text="Context")
        self.tree.heading("Status", text="Status")
        
        self.tree.column("Select", width=50, anchor=tk.CENTER, stretch=False)
        self.tree.column("Source Path", width=400, anchor=tk.W, stretch=True)
        self.tree.column("Target Path", width=400, anchor=tk.W, stretch=True)
        self.tree.column("Context", width=200, anchor=tk.W, stretch=False)
        self.tree.column("Status", width=150, anchor=tk.W, stretch=False)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=y_scroll.set)

        x_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(xscrollcommand=x_scroll.set)

        # Bottom actions
        act = ttk.Frame(self)
        act.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=8)
        self.progress = ttk.Progressbar(act, orient=tk.HORIZONTAL, mode="determinate", maximum=100, variable=self.progress_var)
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,8))
        ttk.Label(act, textvariable=self.status_var).pack(side=tk.LEFT)

        exp = ttk.Frame(self)
        exp.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0,8))
        ttk.Button(exp, text="Export List", command=self._on_export_list).pack(side=tk.LEFT)
        ttk.Button(exp, text="Organize", command=self._on_organize).pack(side=tk.LEFT, padx=(8,0))

    def _on_choose_folder(self):
        folder = filedialog.askdirectory(title="Choose a folder to scan")
        if not folder:
            return
        self.folder = Path(folder)
        self.root_name = self.folder.name
        self.folder_lbl.configure(text=str(self.folder))
        self.status_var.set("Analyzing folder structure...")
        
        # Initialize enhanced analyzer
        self.analyzer = EnhancedFileAnalyzer(self.folder)
        self.status_var.set("Ready.")
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
        backend = self.selected_backend.get()
        model = self.selected_model.get().strip()
        api_key = self.api_key.get().strip()
        
        ok, msg = test_ai_connection(backend, model, api_key)
        if ok:
            messagebox.showinfo("AI Connection", msg or "Connection successful!")
        else:
            messagebox.showerror("AI Connection", msg or "Connection failed!")

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
                messagebox.showinfo("Cache cleared", "Deleted history file and reset cache.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete cache file: {e}")
        else:
            self.history = {}
            messagebox.showinfo("Cache cleared", "No cache file found; in-memory cache reset.")

    def _start_scan(self):
        if not self.folder:
            messagebox.showwarning("No folder", "Please choose a folder first.")
            return
        if self.scanning:
            return

        # per-run temp JSONL log
        try:
            tmpdir = Path(tempfile.gettempdir())
            self.tmp_scan_path = tmpdir / f"enhanced_ai_scan_{int(time.time())}.jsonl"
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
        for (_, _, checked, _, _) in self.file_items:
            checked.set(v)

    def _on_organize(self):
        sel = [(s, t, c, st, ctx) for (s, t, c, st, ctx) in self.file_items if c.get()]
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
            filetypes=[("CSV", "*.csv"), ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["checked", "source", "target", "context", "status"])
                for (src, tgt, chk, st, ctx) in self.file_items:
                    w.writerow([bool(chk.get()), str(src), tgt, ctx, st])
            messagebox.showinfo("Exported", f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Export error", str(e))

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

            future_to_file: Dict = {}
            for f in files:
                if not self.scanning or self.cancel_event.is_set():
                    break
                fut = self.executor.submit(
                    self._process_file_enhanced, f, backend, model, api_key,
                    self.ignore_cache_this_run
                )
                self.current_futures.add(fut)
                future_to_file[fut] = f

            completed = 0
            for fut in as_completed(future_to_file):
                if not self.scanning or self.cancel_event.is_set():
                    break
                src = future_to_file[fut]
                try:
                    final_path, status, context = fut.result()
                except Exception as e:
                    final_path, status, context = "Uncategorized", f"Error: {e}", ""

                checked = tk.BooleanVar(value=True)
                entry = (src, final_path, checked, status, context)
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
        self.status_var.set("Scan cancelled." if self.cancel_event.is_set() else "Enhanced scan complete.")
        self.ignore_cache_this_run = False

    def _process_file_enhanced(self, file_path: Path, backend: str, model: str, api_key: str,
                              ignore_cache: bool) -> Tuple[str, str, str]:
        if self.cancel_event.is_set():
            return "Uncategorized", "Cancelled", ""

        # Generate enhanced signature
        sig = self._enhanced_signature(file_path)
        
        # Get comprehensive context
        context = self.analyzer.get_file_context(file_path) if self.analyzer else {}
        context_summary = self._get_context_summary(file_path)

        # Check cache first
        if not ignore_cache and sig in self.history:
            cached_result = self.history[sig]
            return cached_result.get("ai_path", "Uncategorized"), "Cached", context_summary

        # Generate enhanced prompt
        prompt = self._build_enhanced_prompt(file_path, context)
        
        # Query AI with enhanced prompt
        try:
            if backend == "Local (Ollama)":
                raw_response = query_ollama(model=model or "llama3.1", prompt=prompt)
            elif backend == "OpenAI":
                raw_response = query_openai(api_key=api_key, model=model or "gpt-4o-mini", prompt=prompt)
            elif backend == "Grok":
                raw_response = query_grok(api_key=api_key, model=model or "grok-2-mini", prompt=prompt)
            else:
                raw_response = "Uncategorized"
        except Exception as e:
            raw_response = f"Error: {e}"

        # Process and validate response
        ai_path = self._process_ai_response(raw_response, file_path, context)
        
        # Refine if enabled
        if self.refine_suggestions_var.get():
            refined_path = self._refine_suggestion(file_path, ai_path, context, backend, model, api_key)
            final_path = refined_path if refined_path else ai_path
            status = "AI suggested → Refined"
        else:
            final_path = ai_path
            status = "AI suggested"

        # Save to history
        self.history[sig] = {
            "ai_path": final_path,
            "fullpath": str(file_path),
            "context": context,
            "timestamp": time.time()
        }
        self._save_history()

        # Log for debugging
        self._append_temp_log({
            "ts": time.time(),
            "source": str(file_path),
            "context": context,
            "raw_response": raw_response,
            "final_path": final_path,
            "status": status
        })

        return final_path, status, context_summary

    def _build_enhanced_prompt(self, file_path: Path, context: Dict[str, str]) -> str:
        """Build a comprehensive prompt considering file context and project structure"""
        
        # Base prompt structure
        prompt_parts = [
            "You are an expert file organizer. Analyze the file and suggest the best folder path for organization.",
            "",
            f"FILE: {file_path.name}",
            f"EXTENSION: {file_path.suffix}",
            f"CURRENT LOCATION: {file_path.parent}",
            f"CATEGORY: {context.get('file_category', 'unknown')}",
            f"PROJECT TYPE: {context.get('project_type', 'unknown')}",
        ]

        # Add context if enabled
        if self.use_context_var.get():
            if context.get('sibling_files'):
                prompt_parts.append(f"SIBLING FILES: {', '.join(context['sibling_files'][:5])}")
            
            if context.get('existing_structure'):
                prompt_parts.append(f"EXISTING STRUCTURE: {context['existing_structure']}")
            
            if context.get('folder_pattern') != 'unknown':
                prompt_parts.append(f"FOLDER PATTERN: {context['folder_pattern']}")

        # Add project-specific guidance
        project_type = context.get('project_type', 'unknown')
        if project_type in ['python', 'nodejs', 'golang', 'rust', 'java_maven', 'java_gradle']:
            prompt_parts.extend([
                "",
                "PROJECT GUIDELINES:",
                "- Keep source code in 'src/' or similar",
                "- Separate tests in 'tests/' or 'test/'",
                "- Configuration files in 'config/' or root",
                "- Documentation in 'docs/' or 'doc/'",
                "- Assets in 'assets/', 'static/', or 'public/'"
            ])
        elif project_type == 'terraform':
            prompt_parts.extend([
                "",
                "PROJECT GUIDELINES:",
                "- Terraform files in 'terraform/' or 'infrastructure/'",
                "- Separate environments (dev, staging, prod)",
                "- Keep modules in 'modules/'",
                "- Variables and outputs in separate files"
            ])

        # Add smart grouping if enabled
        if self.smart_grouping_var.get():
            prompt_parts.extend([
                "",
                "SMART GROUPING RULES:",
                "- Group related files together",
                "- Consider file dependencies",
                "- Maintain logical hierarchy",
                "- Use descriptive folder names"
            ])

        # Final instructions
        prompt_parts.extend([
            "",
            "RESPONSE FORMAT:",
            "- Return ONLY the folder path (e.g., 'src/components' or 'docs/api')",
            "- Use forward slashes (/)",
            "- Keep paths concise (1-3 levels)",
            "- If uncertain, use 'Uncategorized'",
            "",
            "SUGGESTED PATH:"
        ])

        return "\n".join(prompt_parts)

    def _process_ai_response(self, response: str, file_path: Path, context: Dict[str, str]) -> str:
        """Process and validate AI response"""
        if not response or response.startswith("Error:"):
            return "Uncategorized"

        # Clean and validate the response
        cleaned = validate_folder_path(response)
        
        # Apply context-aware adjustments
        if self.consider_structure_var.get():
            cleaned = self._adjust_for_project_structure(cleaned, context)
        
        return cleaned

    def _adjust_for_project_structure(self, path: str, context: Dict[str, str]) -> str:
        """Adjust path based on existing project structure"""
        project_type = context.get('project_type', 'unknown')
        
        # Adjust based on project type
        if project_type in ['python', 'nodejs']:
            if path.startswith('src/') and 'src' not in context.get('existing_structure', {}):
                # If no src folder exists, consider alternatives
                if 'app' in context.get('existing_structure', {}):
                    path = path.replace('src/', 'app/', 1)
                elif 'lib' in context.get('existing_structure', {}):
                    path = path.replace('src/', 'lib/', 1)
        
        # Adjust based on folder patterns
        folder_pattern = context.get('folder_pattern', 'unknown')
        if folder_pattern == 'kebab_case':
            # Convert to kebab case if that's the project pattern
            path = path.replace('_', '-').lower()
        elif folder_pattern == 'snake_case':
            # Convert to snake case
            path = path.replace('-', '_').lower()
        
        return path

    def _refine_suggestion(self, file_path: Path, initial_path: str, context: Dict[str, str],
                          backend: str, model: str, api_key: str) -> Optional[str]:
        """Refine the initial AI suggestion"""
        if not initial_path or initial_path == "Uncategorized":
            return None

        refine_prompt = f"""
You are refining a file organization suggestion. The current suggestion is good, but can be improved.

FILE: {file_path.name}
CURRENT SUGGESTION: {initial_path}
CONTEXT: {context.get('file_category', 'unknown')} file in {context.get('project_type', 'unknown')} project

RULES:
- Only improve if the suggestion can be made more specific or logical
- Keep the same general structure if it's already good
- Consider the project type and existing patterns
- Return ONLY the improved path or the original if no improvement needed

IMPROVED PATH:"""

        try:
            if backend == "Local (Ollama)":
                refined = query_ollama(model=model or "llama3.1", prompt=refine_prompt)
            elif backend == "OpenAI":
                refined = query_openai(api_key=api_key, model=model or "gpt-4o-mini", prompt=refine_prompt)
            elif backend == "Grok":
                refined = query_grok(api_key=api_key, model=model or "grok-2-mini", prompt=refine_prompt)
            else:
                return None
        except Exception:
            return None

        refined = validate_folder_path(refined)
        if refined and refined != "Uncategorized" and refined != initial_path:
            return refined
        
        return None

    def _get_context_summary(self, file_path: Path) -> str:
        """Get a brief context summary for display"""
        if not self.analyzer:
            return ""
        
        context = self.analyzer.get_file_context(file_path)
        parts = []
        
        if context.get('file_category') != 'unknown':
            parts.append(context['file_category'])
        
        if context.get('project_type') != 'unknown':
            parts.append(context['project_type'])
        
        if context.get('depth', 0) > 2:
            parts.append(f"depth:{context['depth']}")
        
        return " | ".join(parts) if parts else ""

    def _enhanced_signature(self, file_path: Path) -> str:
        """Generate enhanced file signature including context"""
        try:
            st = file_path.stat()
            basic_sig = f"{file_path.name}|{st.st_size}|{int(st.st_mtime)}"
            
            # Add context hash if analyzer is available
            if self.analyzer:
                context = self.analyzer.get_file_context(file_path)
                context_str = f"{context.get('project_type', '')}|{context.get('file_category', '')}|{context.get('parent_dir', '')}"
                context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
                return f"{basic_sig}|{context_hash}"
            
            return basic_sig
        except Exception:
            return f"{file_path.name}|0|0"

    def _add_file_to_tree(self, entry: Tuple[Path, str, tk.BooleanVar, str, str]):
        src, ai_path, checked, status, context = entry
        checkbox = "☑" if checked.get() else "☐"
        iid = self.tree.insert("", "end",
                              values=(checkbox, str(src), ai_path, context, status))
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

    def _organize_files_async(self, selected_files, dest_path: Path):
        def organize():
            success = errors = 0
            total = len(selected_files)

            for i, (src, tgt, chk, st, _) in enumerate(selected_files):
                if not chk.get():
                    continue
                    
                try:
                    tpath = Path(tgt)
                    tdir = dest_path / tpath
                    tdir.mkdir(parents=True, exist_ok=True)
                    
                    target = tdir / src.name
                    n = 1
                    while target.exists():
                        target = tdir / f"{src.stem}_{n}{src.suffix}"
                        n += 1
                        
                    shutil.move(str(src), str(target))
                    success += 1
                except Exception as e:
                    print(f"Error organizing {src}: {e}")
                    errors += 1

                prog = int((i + 1) * 100 / total)
                self.after(0, lambda p=prog: self.progress_var.set(p))
                self.after(0, lambda s=success, e=errors: self.status_var.set(f'Organizing... Success: {s}, Errors: {e}'))

            self.after(0, lambda: self.progress_var.set(0))
            self.after(0, lambda: self.status_var.set(f"Organization complete! Success: {success}, Errors: {errors}"))
            
            if errors == 0:
                self.after(0, lambda: messagebox.showinfo("Success", f"All {success} item(s) organized!"))
            else:
                self.after(0, lambda: messagebox.showwarning("Completed with Errors",
                                                           f"Organized {success} item(s), {errors} failed."))

        threading.Thread(target=organize, daemon=True).start()

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

    def _load_history(self):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except Exception:
            self.history = {}

    def _save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass

    def _load_rules(self):
        try:
            with open(RULES_FILE, "r", encoding="utf-8") as f:
                self.rules = json.load(f)
        except Exception:
            self.rules = {}

    def _on_close(self):
        try:
            self._on_cancel_scan()
        except Exception:
            pass
        try:
            self.executor.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            try:
                self.executor.shutdown(wait=False)
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    app = EnhancedAIOrganizer()
    app.mainloop()