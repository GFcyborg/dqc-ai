"""
Main GUI window for DQC - OpenQASM Splitter
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from pathlib import Path
import requests
import re
from typing import Dict, List, Optional, Tuple
import json
import sys
import threading
from threading import Thread
import queue

from parser import QasmParser
from analyzer import VariableAnalyzer
try:
    from choreo.controller import Controller
except ImportError:
    Controller = None

try:
    from stdlib import get_stdlib_content
except ImportError:
    # Fallback if stdlib not available
    def get_stdlib_content(filename: str) -> str:
        return f"// Standard library file '{filename}' not available\n"


class QasmAnalyzerGUI:
    """Main application window"""
    
    # GitHub API endpoint for listing examples
    EXAMPLES_API_URL = "https://api.github.com/repos/openqasm/openqasm/contents/examples"
    EXAMPLES_RAW_URL = "https://raw.githubusercontent.com/openqasm/openqasm/main/examples/"
    
    # Standard library URL
    STDLIBRARY_BASE_URL = "https://raw.githubusercontent.com/openqasm/openqasm/main/lib/"
    
    def __init__(self, root):
        self.root = root
        self.root.title("DQC - OpenQASM Splitter")
        self.root.geometry("1200x800")
        
        self.parser = None
        self.analyzer = VariableAnalyzer()
        self.current_file = None
        self.source_code = ""
        self.split_points = set()
        self.code_font = ('Courier', 10)
        self.include_files = {}
        self.include_tabs = {}
        self.replicate_includes = tk.BooleanVar(value=False)
        self.example_files = {}
        self._status_timers = {'blink': None, 'toggle': None}
        self._status_visible = True
        self._status_message = ""
        
        try:
            self.parser = QasmParser()
        except RuntimeError as e:
            self._show_messagebox(
                messagebox.showerror,
                "Parser Not Available",
                f"{e}\n\nYou can still use the variable analyzer without AST display."
            )
        
        self._setup_ui()
    
    def _setup_ui(self):
        self._setup_menu()
        self._setup_main_layout()
    
    def _setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Local File...", command=self._open_local_file)
        file_menu.add_separator()
        
        self.examples_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Load Example", menu=self.examples_menu)
        self.examples_menu.add_command(label="Loading examples...", state='disabled')
        self.root.after(100, self._load_examples_from_github)
        
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Controller mode menu
        controller_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Controller Mode", menu=controller_menu)
        controller_menu.add_command(label="Distribute chunks to workers", 
                        command=self._launch_controller_mode,
                        state='normal' if Controller else 'disabled')
        controller_menu.add_command(label="Run remote chunks", 
                        command=self._launch_remote_chunks_dialog)
    
    def _setup_main_layout(self):
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        self.file_label = ttk.Label(main_frame, text="No file loaded", 
                                   font=('Arial', 10, 'bold'))
        self.file_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self._setup_source_panel(paned)
        self._setup_analysis_panel(paned)
        self._setup_control_frame(main_frame)
    
    def _setup_source_panel(self, paned):
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=2)
        
        ttk.Label(left_frame, text="Source Code (click lines to mark split points)", 
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        source_container = ttk.Frame(left_frame)
        source_container.pack(fill=tk.BOTH, expand=True)
        
        self.line_numbers = tk.Text(source_container, width=4, padx=3, takefocus=0,
                                    border=0, background='lightgray', state='disabled',
                                    font=self.code_font)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        self.source_text = scrolledtext.ScrolledText(source_container, wrap=tk.NONE,
                                                     font=self.code_font)
        self.source_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.source_text.bind('<Button-1>', self._on_line_click)
        self.source_text.config(yscrollcommand=self._on_text_scroll)
    
    def _setup_analysis_panel(self, paned):
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self._add_ast_tab()
        self._add_analysis_tab()
    
    def _add_ast_tab(self):
        ast_frame = ttk.Frame(self.notebook)
        self.notebook.add(ast_frame, text="AST")
        
        tree_frame = ttk.Frame(ast_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        ast_yscroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        ast_xscroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        self.ast_tree = ttk.Treeview(tree_frame,
                                     yscrollcommand=ast_yscroll.set,
                                     xscrollcommand=ast_xscroll.set,
                                     selectmode='browse')
        
        ast_yscroll.config(command=self.ast_tree.yview)
        ast_xscroll.config(command=self.ast_tree.xview)
        
        ast_yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        ast_xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.ast_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.ast_tree['columns'] = ('line', 'text')
        self.ast_tree.column('#0', width=300, minwidth=200)
        self.ast_tree.column('line', width=80, minwidth=50)
        self.ast_tree.column('text', width=400, minwidth=100)
        
        self.ast_tree.heading('#0', text='Node Type', anchor=tk.W)
        self.ast_tree.heading('line', text='Line', anchor=tk.W)
        self.ast_tree.heading('text', text='Text', anchor=tk.W)
    
    def _add_analysis_tab(self):
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Variable Analysis")
        
        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, wrap=tk.WORD,
                                                       font=self.code_font)
        self.analysis_text.pack(fill=tk.BOTH, expand=True)
    
    def _setup_control_frame(self, main_frame):
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(control_frame, text="Clear Split Points",
                  command=self._clear_split_points).pack(side=tk.LEFT, padx=5)
        
        self.save_button = tk.Button(control_frame, text="✓ Analyze & Save Chunks",
                  command=self._save_chunks, bg='#4CAF50', fg='white',
                  font=('Arial', 10, 'bold'), relief=tk.RAISED, bd=2,
                  padx=10, pady=5, cursor='hand2')
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(control_frame, text="Replicate includes in all chunks",
                       variable=self.replicate_includes).pack(side=tk.LEFT, padx=15)
        
        self.status_label = ttk.Label(control_frame, text="Ready")
        self.status_label.pack(side=tk.RIGHT, padx=5)
    
    def _on_text_scroll(self, *args):
        self.line_numbers.yview_moveto(args[0])
    
    def _on_line_click(self, event):
        index = self.source_text.index(f"@{event.x},{event.y}")
        line_num = int(index.split('.')[0])

        if not self._is_split_point_allowed(line_num):
            self._show_status("Split points must be at top level (not inside a block).", blink=True)
            return
        
        self.split_points.symmetric_difference_update({line_num})
        self._update_split_point_display()
        self._update_analysis()
    
    def _update_split_point_display(self):
        self.source_text.tag_remove('split_point', '1.0', tk.END)
        self.source_text.tag_config('split_point', background='yellow', foreground='black')
        for line_num in self.split_points:
            self.source_text.tag_add('split_point', f'{line_num}.0', f'{line_num}.end+1c')
    
    def _clear_split_points(self):
        self.split_points.clear()
        self._update_split_point_display()
        self._update_analysis()

    def _show_status(self, message: str, blink: bool = False):
        for timer_id in self._status_timers.values():
            if timer_id:
                self.root.after_cancel(timer_id)
        self._status_timers = {'blink': None, 'toggle': None}
        
        self._status_message = message
        self.status_label.config(text=message, foreground='black')
        self._status_visible = True
        
        if blink:
            self._blink_status_toggle()
            self._status_timers['blink'] = self.root.after(3000, self._stop_blink_and_gray)
    
    def _blink_status_toggle(self):
        self._status_visible = not self._status_visible
        self.status_label.config(text=self._status_message if self._status_visible else '')
        self._status_timers['toggle'] = self.root.after(500, self._blink_status_toggle)
    
    def _stop_blink_and_gray(self):
        if self._status_timers['toggle']:
            self.root.after_cancel(self._status_timers['toggle'])
            self._status_timers['toggle'] = None
        self.status_label.config(text=self._status_message, foreground='gray')

    def _focus_window(self, window: tk.Misc, keep_on_top: bool = False) -> None:
        try:
            was_topmost = window.attributes('-topmost')
        except Exception:
            was_topmost = None

        try:
            window.lift()
            window.focus_force()
            window.attributes('-topmost', True)
            if not keep_on_top and not was_topmost:
                window.after(200, lambda: window.attributes('-topmost', False))
        except Exception:
            # Best-effort focus; ignore if not supported in current environment
            pass

    def _show_messagebox(self, func, title: str, message: str, parent: Optional[tk.Misc] = None, **kwargs):
        dialog_parent = parent or self.root
        self._focus_window(dialog_parent)
        return func(title, message, parent=dialog_parent, **kwargs)

    def _is_split_point_allowed(self, line_num: int) -> bool:
        source_lines = self.source_text.get('1.0', tk.END).splitlines()
        if line_num < 1 or line_num > len(source_lines):
            return False
        return self._compute_block_depths(source_lines)[line_num - 1] == 0

    @staticmethod
    def _compute_block_depths(lines: List[str]) -> List[int]:
        depths, depth = [], 0
        for line in lines:
            depths.append(max(depth, 0))
            depth += QasmAnalyzerGUI._brace_delta(line)
        return depths

    @staticmethod
    def _brace_delta(line: str) -> int:
        delta = 0
        in_string = None
        i = 0

        while i < len(line):
            ch = line[i]

            if in_string:
                if ch == in_string and (i == 0 or line[i - 1] != '\\'):
                    in_string = None
                i += 1
                continue

            if ch in ('"', "'"):
                in_string = ch
                i += 1
                continue

            if ch == '/' and i + 1 < len(line) and line[i + 1] == '/':
                break

            if ch == '{':
                delta += 1
            elif ch == '}':
                delta -= 1

            i += 1

        return delta
    
    @staticmethod
    def _extract_includes(qasm_content: str) -> List[str]:
        return re.compile(r'^\s*include\s+["\']([^"\']+)["\']\s*;', 
                         re.MULTILINE | re.IGNORECASE).findall(qasm_content)
    
    def _download_include_file(self, filename: str, split_out_dir: Path = None) -> Tuple[bool, str]:
        urls = [f"{self.STDLIBRARY_BASE_URL}{filename}",
                f"https://raw.githubusercontent.com/openqasm/openqasm/develop/lib/{filename}"]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    content = response.text
                    self.include_files[filename] = content
                    if split_out_dir:
                        try:
                            (split_out_dir / filename).write_text(content, encoding='utf-8')
                        except Exception as e:
                            print(f"Warning: Could not save {filename} to disk: {e}")
                    return True, content
            except Exception:
                continue
        
        try:
            fallback = get_stdlib_content(filename)
            if fallback and not fallback.startswith("// Standard library file"):
                self.include_files[filename] = fallback
                if split_out_dir:
                    try:
                        (split_out_dir / filename).write_text(fallback, encoding='utf-8')
                    except Exception as e:
                        print(f"Warning: Could not save {filename} to disk: {e}")
                return True, fallback
        except Exception:
            pass
        
        print(f"Warning: Could not download {filename}")
        return False, f"Could not download {filename} - network unavailable"
    
    def _add_include_tabs(self, split_out_dir: Path = None):
        for filename in list(self.include_tabs.keys()):
            self.notebook.forget(self.include_tabs[filename])
        self.include_tabs.clear()
        
        for filename in self._extract_includes(self.source_code):
            success, content = self._download_include_file(filename, split_out_dir)
            
            include_frame = ttk.Frame(self.notebook)
            include_text = scrolledtext.ScrolledText(include_frame, wrap=tk.NONE,
                                                    font=self.code_font)
            include_text.pack(fill=tk.BOTH, expand=True)
            
            if success:
                include_text.insert('1.0', content)
                tab_label = filename
            else:
                error_msg = f"⚠ Could not download '{filename}' from OpenQASM repository\n\n"
                error_msg += f"Error: {content}\n\n"
                error_msg += "The library file is referenced but not available.\n"
                error_msg += "You may need to:\n"
                error_msg += "1. Check your internet connection\n"
                error_msg += "2. Provide the file manually in the split-out directory\n"
                error_msg += "3. Use the code locally where the library is available"
                include_text.insert('1.0', error_msg)
                tab_label = f"{filename} ⚠"
            
            include_text.config(state='disabled')
            self.notebook.add(include_frame, text=tab_label)
            self.include_tabs[filename] = include_frame
    
    def _load_examples_from_github(self):
        try:
            response = requests.get(self.EXAMPLES_API_URL, timeout=5)
            response.raise_for_status()
            
            qasm_files = [(f['name'], self.EXAMPLES_RAW_URL + f['name']) 
                         for f in response.json() if f['name'].endswith('.qasm')]
            
            self.examples_menu.delete(0, tk.END)
            
            if qasm_files:
                qasm_files.sort(key=lambda x: x[0])
                for filename, url in qasm_files:
                    display_name = filename[:-5].replace('_', ' ').replace('-', ' ').title()
                    self.examples_menu.add_command(
                        label=f"{display_name}  ({filename})",
                        command=lambda u=url, n=filename: self._load_from_url(u, n))
                self.example_files = dict(qasm_files)
            else:
                self.examples_menu.add_command(label="No examples found", state='disabled')
                
        except Exception as e:
            print(f"Failed to load examples from GitHub: {e}")
            self.examples_menu.delete(0, tk.END)
            self.examples_menu.add_command(label="Could not load examples", state='disabled')
    
    def _open_local_file(self):
        split_out_dir = Path.cwd() / "split-out"
        split_out_dir.mkdir(parents=True, exist_ok=True)
        
        filename = filedialog.askopenfilename(
            title="Select QASM file",
            initialdir=str(split_out_dir),
            filetypes=[("QASM/DQC files", "*.qasm *.dqc"), ("QASM files", "*.qasm"),
                      ("DQC files", "*.dqc"), ("All files", "*.*")])
        if filename:
            self._load_file(filename)
    
    def _load_from_url(self, url: str, name: str):
        try:
            self._show_status(f"Downloading {name}...")
            self.root.update()
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            self.source_code = response.text
            self.current_file = name
            split_out_dir = Path.cwd() / "split-out"
            
            self._display_code()
            self._add_include_tabs(split_out_dir)
            self._show_status(f"Loaded: {name}")
        except Exception as e:
            self._show_messagebox(messagebox.showerror, "Download Error", f"Failed to download file:\n{e}")
            self._show_status("Error")
    
    @staticmethod
    def _parse_dqc_content(content: str):
        split_points = []
        output_lines = []
        split_pattern = re.compile(r"^\s*pragma\s+dqc\.v0\.split\s+id=(\d+)\s*$")

        for line in content.splitlines():
            if split_pattern.match(line):
                split_points.append(len(output_lines) + 1)
            else:
                output_lines.append(line)

        max_line = len(output_lines)
        return "\n".join(output_lines), [sp for sp in split_points if 1 <= sp <= max_line]

    def _load_file(self, filepath: str):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            path = Path(filepath)
            if filepath.endswith('.dqc'):
                self.source_code, split_points = self._parse_dqc_content(content)
                self.current_file = str(path.with_suffix(''))
                self._display_code()
                self.split_points = set(split_points)
                self._update_split_point_display()
                self._update_analysis()
            else:
                self.source_code = content
                self.current_file = filepath
                self._display_code()
            
            self._show_status(f"Loaded: {path.name}")
        except Exception as e:
            self._show_messagebox(messagebox.showerror, "File Error", f"Failed to load file:\n{e}")
            self._show_status("Error")
    
    def _display_code(self):
        self.split_points.clear()
        
        if isinstance(self.current_file, str):
            display_name = Path(self.current_file).name if Path(self.current_file).exists() else self.current_file
        else:
            display_name = str(self.current_file)
        self.file_label.config(text=f"File: {display_name}")
        
        self.source_text.config(state='normal')
        self.source_text.delete('1.0', tk.END)
        self.source_text.insert('1.0', self.source_code)
        
        num_lines = self.source_code.count('\n') + 1
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        self.line_numbers.insert('1.0', '\n'.join(str(i) for i in range(1, num_lines + 1)))
        self.line_numbers.config(state='disabled')
        
        self._update_ast()
        self._add_include_tabs()
        
        self.analysis_text.delete('1.0', tk.END)
        self.analysis_text.insert('1.0', "Mark split points in the source code to see variable analysis.")
    
    def _update_ast(self):
        for item in self.ast_tree.get_children():
            self.ast_tree.delete(item)
        
        if not self.parser:
            self.ast_tree.insert('', 'end', text="Parser not available. Run 'gradle generateGrammarSource' first.",
                               values=('', ''))
            return
        
        try:
            result = self.parser.parse_string(self.source_code)
            
            if result.errors:
                error_node = self.ast_tree.insert('', 'end', text='Parse Errors', values=('', ''))
                for error in result.errors:
                    self.ast_tree.insert(error_node, 'end', text=error, values=('', ''))
            
            if result.ast:
                self._populate_ast_tree('', result.ast)
            else:
                self.ast_tree.insert('', 'end', text='No AST generated', values=('', ''))
        except Exception as e:
            self.ast_tree.insert('', 'end', text=f'Error parsing: {e}', values=('', ''))
    
    def _populate_ast_tree(self, parent, ast_node, max_text_len=50):
        if ast_node is None:
            return
        
        node_type = ast_node.get('type', 'unknown')
        line_info = str(ast_node.get('line', '')) if 'line' in ast_node else ''
        text = ast_node.get('text', '')
        if len(text) > max_text_len:
            text = text[:max_text_len - 3] + "..."
        
        node_id = self.ast_tree.insert(parent, 'end', text=node_type, values=(line_info, text))
        
        for child in ast_node.get('children', []):
            self._populate_ast_tree(node_id, child, max_text_len)
    
    def _update_analysis(self):
        if not self.split_points:
            self.analysis_text.delete('1.0', tk.END)
            self.analysis_text.insert('1.0', "Mark split points in the source code to see variable analysis.")
            return
        
        self.analysis_text.delete('1.0', tk.END)
        for i, chunk in enumerate(self.analyzer.analyze(self.source_code, list(self.split_points))):
            self.analysis_text.insert(tk.END, f"=== Chunk {i} (lines {chunk.start_line}-{chunk.end_line}) ===\n")
            
            if chunk.required_variables:
                self.analysis_text.insert(tk.END, "Required variables:\n")
                for var in chunk.required_variables:
                    self.analysis_text.insert(tk.END, f"  - {var} (defined at line {var.defined_at})\n")
            else:
                self.analysis_text.insert(tk.END, "No external variables required\n")
            
            self.analysis_text.insert(tk.END, "\n")
    
    def _save_chunks(self):
        if not self.split_points:
            self._show_messagebox(messagebox.showwarning, "No Split Points", "Please mark at least one split point.")
            return
        
        if not self.current_file:
            self._show_messagebox(messagebox.showwarning, "No File", "Please load a file first.")
            return
        
        base_name, original_filename = self._get_filenames()
        split_out_root = Path.cwd() / "split-out"
        output_dir = split_out_root / base_name
        
        try:
            split_out_root.mkdir(parents=True, exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._show_messagebox(messagebox.showerror, "Error", f"Failed to create output directory:\n{e}")
            return
        
        try:
            self._save_include_and_original_files(split_out_root, original_filename)
            self._save_dqc_with_pragmas(split_out_root, original_filename)
            self._save_chunks_to_files(output_dir, base_name)
            
            chunks_count = len(self.analyzer.analyze(self.source_code, list(self.split_points)))
            self._show_messagebox(messagebox.showinfo, "Success", f"Saved {chunks_count} chunks to:\n{output_dir}")
            self._show_status(f"Saved {chunks_count} chunks to {output_dir}")
        except Exception as e:
            self._show_messagebox(messagebox.showerror, "Error", f"Failed to save chunks:\n{e}")
    
    def _get_filenames(self) -> Tuple[str, str]:
        path = Path(self.current_file)
        if path.suffix in [".qasm", ".dqc"] or path.name.endswith(".qasm.dqc"):
            original = path.name if path.name.endswith(".dqc") else path.name
            base = path.stem.replace(".qasm", "") if ".qasm" in path.stem else path.stem
        elif path.exists():
            base, original = path.stem, path.name
        else:
            base = self.current_file.replace(" ", "_").lower()
            if base.endswith(".qasm"):
                base = Path(base).stem
            original = f"{base}.qasm"
        
        return base, original
    
    def _save_include_and_original_files(self, split_out_root: Path, original_filename: str):
        for filename, content in self.include_files.items():
            (split_out_root / filename).write_text(content, encoding='utf-8')
        (split_out_root / original_filename).write_text(self.source_code, encoding='utf-8')
    
    def _save_dqc_with_pragmas(self, split_out_root: Path, original_filename: str):
        split_points_sorted = sorted(set(self.split_points))
        split_map = {sp: i + 1 for i, sp in enumerate(split_points_sorted) if sp >= 1}
        
        dqc_path = split_out_root / f"{original_filename}.dqc"
        with open(dqc_path, 'w', encoding='utf-8') as f:
            for line_num, line in enumerate(self.source_code.splitlines(), start=1):
                if line_num in split_map:
                    f.write(f"pragma dqc.v0.split id={split_map[line_num]}\n")
                f.write(f"{line}\n")
    
    def _save_chunks_to_files(self, output_dir: Path, base_name: str):
        # Clean up previous numbered chunks to avoid leftover files
        if output_dir.exists():
            for old_chunk in output_dir.glob('*.qasm'):
                # Only remove numbered chunk files (0.qasm, 1.qasm, etc.)
                if old_chunk.stem.isdigit():
                    try:
                        old_chunk.unlink()
                    except Exception as e:
                        print(f"Warning: Could not remove old chunk {old_chunk}: {e}")
        
        chunks = self.analyzer.analyze(self.source_code, list(self.split_points))
        include_lines = self._get_include_lines_if_replicate()
        
        for i, chunk in enumerate(chunks):
            chunk_file = output_dir / f"{i}.qasm"
            chunk_has_includes = any(re.match(r'^\s*include\s+', line, re.IGNORECASE)
                                    for line in chunk.source_lines)
            
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(f"// Chunk {i} of {len(chunks) - 1} from {base_name}.qasm\n")
                
                if chunk.required_variables:
                    f.write("// Required variables:\n")
                    for var in chunk.required_variables:
                        f.write(f"//   {var}\n")
                    f.write("\n")
                
                if include_lines and not chunk_has_includes:
                    f.write('\n'.join(include_lines) + "\n\n")
                
                f.write('\n'.join(chunk.source_lines))
    
    def _get_include_lines_if_replicate(self) -> List[str]:
        if not self.replicate_includes.get():
            return []
        return [line.strip() for line in self.source_code.splitlines()
                if re.match(r'^\s*include\s+["\']([^"\']+)["\']\s*;', line, re.IGNORECASE)]
    
    def _launch_controller_mode(self):
        """Launch the controller mode to distribute chunks to worker nodes."""
        if not Controller:
            self._show_messagebox(
                messagebox.showerror,
                "Controller Not Available",
                "Controller module not available. Make sure choreo.controller is properly installed."
            )
            return
        
        self._show_controller_dialog()

    def _launch_remote_chunks_dialog(self):
        """Placeholder dialog for running remote chunks."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Controller Mode - Run Remote Chunks")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        self._focus_window(dialog)

        content_frame = ttk.Frame(dialog, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(content_frame, text="Run remote chunks is not implemented yet.")\
            .pack(pady=(0, 20))

        ttk.Button(content_frame, text="Close", command=dialog.destroy).pack()
    
    def _custom_ask_directory(self, title="Select a Directory", initialdir=None):
        """Custom directory selection dialog with single-click selection."""
        selected_dir = [None]  # Use list to allow modification in nested functions
        
        # Create a top-level window for directory selection
        dir_dialog = tk.Toplevel(self.root)
        dir_dialog.title(title)
        dir_dialog.geometry("700x600")
        
        # Make dialog modal and always on top
        dir_dialog.transient(self.root)
        dir_dialog.grab_set()
        dir_dialog.attributes('-topmost', True)
        self._focus_window(dir_dialog, keep_on_top=True)
        
        # Start from initial directory
        if initialdir is None:
            current_path = Path.cwd()
        else:
            current_path = Path(initialdir) if isinstance(initialdir, str) else initialdir
        
        # Current path label - right-aligned to show trailing path
        path_var = tk.StringVar(value=str(current_path))
        path_frame = ttk.Frame(dir_dialog)
        path_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(path_frame, text="Current Path:").pack(side=tk.LEFT)
        path_label = ttk.Label(path_frame, textvariable=path_var, relief=tk.SUNKEN, wraplength=400, justify=tk.RIGHT)
        path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Treeview for directory structure
        tree_frame = ttk.Frame(dir_dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree = ttk.Treeview(tree_frame, yscrollcommand=scrollbar.set, height=20)
        scrollbar.config(command=tree.yview)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Define columns
        tree.column("#0", width=600)
        tree.heading("#0", text="Directories")
        
        # Store path info for each item
        item_paths = {}
        
        def populate_tree(parent_item, parent_path):
            """Recursively populate tree with subdirectories."""
            try:
                # Get directories in current path
                dirs = sorted([d for d in parent_path.iterdir() if d.is_dir()])
                
                for dir_path in dirs:
                    # Skip hidden directories
                    if dir_path.name.startswith('.'):
                        continue
                    
                    item_id = tree.insert(parent_item, "end", text=dir_path.name, open=False)
                    item_paths[item_id] = dir_path
                    
                    # Add a dummy child to show expand arrow
                    tree.insert(item_id, "end", text="loading...", open=False)
            except PermissionError:
                pass
        
        def on_tree_expand(event):
            """Handle tree expansion to load subdirectories on demand."""
            item = tree.selection()[0] if tree.selection() else None
            if not item:
                return
            
            # Clear dummy items and load real subdirectories
            children = tree.get_children(item)
            for child in children:
                tree.delete(child)
            
            path = item_paths.get(item)
            if path and path.is_dir():
                populate_tree(item, path)
        
        def on_tree_click(event):
            """Handle click on tree - select directory immediately."""
            # Get the item that was clicked on
            item = tree.identify('item', event.x, event.y)
            if not item or item not in item_paths:
                return
            
            selected_path = item_paths[item]
            selected_dir[0] = str(selected_path)
            # Close dialog after short delay to allow the click to register
            dir_dialog.after(100, dir_dialog.destroy)
        
        def on_tree_double_click(event):
            """Handle double-click on tree to expand/navigate."""
            # Get the item that was clicked on
            item = tree.identify('item', event.x, event.y)
            if not item or item not in item_paths:
                return
            
            # Expand if not already expanded
            if not tree.item(item, 'open'):
                tree.item(item, open=True)
                # Trigger expand event manually
                tree.event_generate("<<TreeviewOpen>>")
        
        tree.bind("<Button-1>", on_tree_click)
        tree.bind("<Double-Button-1>", on_tree_double_click)
        tree.bind("<<TreeviewOpen>>", on_tree_expand)
        
        # Initialize tree with root
        populate_tree("", current_path)
        
        # Add "Up" button
        control_frame = ttk.Frame(dir_dialog)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def go_up():
            """Go up one directory level."""
            nonlocal current_path
            if current_path.parent != current_path:
                current_path = current_path.parent
                path_var.set(str(current_path))
                # Refresh tree
                tree.delete(*tree.get_children())
                item_paths.clear()
                populate_tree("", current_path)
        
        ttk.Button(control_frame, text="⬆ Up", command=go_up).pack(side=tk.LEFT, padx=2)
        
        # Buttons frame
        button_frame = ttk.Frame(dir_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def cancel():
            """Cancel directory selection."""
            selected_dir[0] = None
            dir_dialog.destroy()
        
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.RIGHT, padx=5)
        
        # Bring dialog to front and focus
        dir_dialog.focus_force()
        dir_dialog.lift()
        
        # Wait for dialog to close
        self.root.wait_window(dir_dialog)
        
        return selected_dir[0]
    
    def _show_controller_dialog(self):
        """Show dialog to select chunks directory and workers_filesrv.json configuration."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Controller Mode - Distribute Chunks to Workers")
        dialog.geometry("600x700")
        dialog.transient(self.root)
        dialog.grab_set()
        self._focus_window(dialog)
        
        # Track original config and whether we're using localhost
        original_config = {}
        temp_localhost_config = {}
        using_localhost = False
        
        # Step 1: Directory selection frame (user must select first)
        dir_frame = ttk.LabelFrame(dialog, text="Step 1: Select Chunks Directory", padding="10")
        dir_frame.pack(fill=tk.X, padx=10, pady=10)
        
        dir_var = tk.StringVar()  # No default - user must select
        ttk.Entry(dir_frame, textvariable=dir_var, state='readonly', width=60).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_dir_button = ttk.Button(dir_frame, text="Browse...")
        browse_dir_button.pack(side=tk.LEFT)
        
        # Workers config file selection frame
        config_frame = ttk.LabelFrame(dialog, text="Workers Configuration File", padding="10")
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        config_var = tk.StringVar()
        
        # Default to choreo/workers_filesrv.json
        default_workers_config = Path(__file__).resolve().parent.parent / "choreo" / "workers_filesrv.json"
        if default_workers_config.exists():
            config_var.set(str(default_workers_config))
        
        ttk.Entry(config_frame, textvariable=config_var, state='readonly', width=60).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_config_button = ttk.Button(config_frame, text="Browse...")
        browse_config_button.pack(side=tk.LEFT)
        
        # Warning label for worker/chunk mismatch
        warning_label = tk.Label(dialog, text="Please select a chunks directory to begin", 
                               font=('Arial', 9, 'italic'), foreground='gray')
        warning_label.pack(fill=tk.X, padx=10, pady=5)
        
        # Step 2: Localhost workers checkbox (initially disabled)
        localhost_frame = ttk.LabelFrame(dialog, text="Step 2: Localhost Configuration (Optional)", padding="10")
        localhost_frame.pack(fill=tk.X, padx=10, pady=10)
        
        use_localhost_var = tk.BooleanVar(value=False)
        localhost_checkbox = ttk.Checkbutton(
            localhost_frame, 
            text="Use localhost as worker nodes (auto-configure ports starting from 6660)",
            variable=use_localhost_var,
            state='disabled'  # Initially disabled until directory is selected
        )
        localhost_checkbox.pack(anchor=tk.W)
        
        # Step 3: Workers preview frame (editable)
        preview_frame = ttk.LabelFrame(dialog, text="Step 3: Workers Configuration Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        preview_text = scrolledtext.ScrolledText(preview_frame, height=10, font=('Courier', 9))
        preview_text.pack(fill=tk.BOTH, expand=True)
        
        def load_original_config():
            """Load the original workers_filesrv.json from disk."""
            nonlocal original_config
            config_path = config_var.get()
            if config_path and Path(config_path).exists():
                try:
                    with open(config_path, 'r') as f:
                        original_config = json.load(f)
                    return original_config
                except Exception as e:
                    print(f"Error loading config: {e}")
                    return {}
            return {}
        
        def update_preview(config_dict=None):
            """Update preview with given config or load from original."""
            if config_dict is None:
                config_dict = load_original_config()
            
            # Remember current state
            current_state = preview_text.cget('state')
            
            # Temporarily enable to update content
            preview_text.config(state='normal')
            preview_text.delete('1.0', tk.END)
            if config_dict:
                preview_text.insert('1.0', json.dumps(config_dict, indent=2))
            else:
                preview_text.insert('1.0', "# No configuration loaded\n# Select a chunks directory and enable localhost,\n# or manually edit the configuration below")
            
            # Restore previous state
            preview_text.config(state=current_state)
        
        def get_current_preview_config():
            """Parse and return the current config from the preview text."""
            try:
                content = preview_text.get('1.0', tk.END).strip()
                if content and not content.startswith('#'):
                    return json.loads(content)
            except Exception as e:
                print(f"Error parsing preview config: {e}")
            return {}
        
        def generate_localhost_config():
            """Generate localhost workers config based on selected chunks directory."""
            nonlocal temp_localhost_config
            chunks_dir = dir_var.get()
            
            if not chunks_dir:
                self._show_messagebox(
                    messagebox.showwarning,
                    "No Directory",
                    "Please select a chunks directory first.",
                    parent=dialog
                )
                use_localhost_var.set(False)
                return None
            
            chunks_dir_path = Path(chunks_dir)
            if not chunks_dir_path.exists() or not chunks_dir_path.is_dir():
                self._show_messagebox(
                    messagebox.showwarning,
                    "Invalid Directory",
                    f"The selected path is not a valid directory:\n{chunks_dir}",
                    parent=dialog
                )
                use_localhost_var.set(False)
                return None
            
            # Count numbered chunk files
            qasm_files = [f for f in chunks_dir_path.glob('*.qasm') if f.stem.isdigit()]
            
            if qasm_files:
                chunk_numbers = [int(f.stem) for f in qasm_files]
                num_chunks = max(chunk_numbers) + 1
            else:
                num_chunks = 0
            
            if num_chunks == 0:
                all_qasm = list(chunks_dir_path.glob('*.qasm'))
                if len(all_qasm) == 0:
                    error_msg = f"No .qasm files found in:\n{chunks_dir}"
                else:
                    error_msg = f"Found {len(all_qasm)} .qasm file(s), but none are numbered chunks:\n"
                    for f in all_qasm[:10]:
                        error_msg += f"  • {f.name}\n"
                    error_msg += f"\nNumbered chunks must be named: 0.qasm, 1.qasm, 2.qasm, etc."
                
                self._show_messagebox(messagebox.showwarning, "No Numbered Chunks", error_msg, parent=dialog)
                use_localhost_var.set(False)
                return None
            
            # Generate localhost workers
            workers = {}
            base_port = 6660
            for i in range(num_chunks):
                workers[str(i)] = f"127.0.0.1:{base_port + i}"
            
            temp_localhost_config = workers
            return workers
        
        def on_localhost_toggle():
            """Handle localhost checkbox toggle."""
            nonlocal using_localhost
            
            if use_localhost_var.get():
                # Generate and show localhost config
                config = generate_localhost_config()
                if config:
                    using_localhost = True
                    update_preview(config)
                    
                    # Make preview non-editable and grayed out
                    preview_text.config(state='disabled', bg='#e0e0e0')
                    
                    warning_label.config(
                        text=f"✓ Generated {len(config)} localhost workers (configuration locked)",
                        foreground='green',
                        font=('Arial', 9, 'bold')
                    )
                else:
                    using_localhost = False
            else:
                # Revert to original config
                using_localhost = False
                update_preview(original_config if original_config else None)
                
                # Make preview editable again
                preview_text.config(state='normal', bg='white')
                
                warning_label.config(
                    text="Using configuration from file (editable)",
                    foreground='gray',
                    font=('Arial', 9, 'italic')
                )
        
        use_localhost_var.trace('w', lambda *args: on_localhost_toggle())
        
        def check_and_display_mismatch():
            """Check for worker/chunk mismatch and update warning label."""
            chunks_dir = dir_var.get()
            
            if not chunks_dir:
                warning_label.config(
                    text="Please select a chunks directory to begin",
                    foreground='gray',
                    font=('Arial', 9, 'italic')
                )
                return
            
            chunks_dir_path = Path(chunks_dir)
            if not chunks_dir_path.exists():
                warning_label.config(text="⚠ Directory not found", foreground='orange', font=('Arial', 9, 'bold'))
                return
            
            # Count only numbered chunk files
            qasm_files = [f for f in chunks_dir_path.glob('*.qasm') if f.stem.isdigit()]
            
            if qasm_files:
                chunk_numbers = [int(f.stem) for f in qasm_files]
                num_chunks = max(chunk_numbers) + 1
            else:
                num_chunks = 0
            
            if num_chunks == 0:
                warning_label.config(
                    text="⚠ No numbered chunk files found in directory",
                    foreground='orange',
                    font=('Arial', 9, 'bold')
                )
                return
            
            # Get current workers config from preview (which may be edited)
            current_config = get_current_preview_config()
            num_workers = len(current_config) if current_config else 0
            
            # Check for mismatch
            if num_workers == 0:
                warning_label.config(
                    text=f"Found {num_chunks} chunks - configure workers",
                    foreground='blue',
                    font=('Arial', 9, 'bold')
                )
            elif num_workers != num_chunks:
                if num_chunks > num_workers:
                    warning_label.config(
                        text=f"🔴 CRITICAL: {num_chunks} chunks but only {num_workers} worker(s)",
                        foreground="red",
                        font=('Arial', 9, 'bold')
                    )
                else:
                    warning_label.config(
                        text=f"⚠ {num_chunks} chunks, {num_workers} workers (extra workers unused)",
                        foreground="orange",
                        font=('Arial', 9, 'bold')
                    )
            else:
                warning_label.config(
                    text=f"✓ Configuration OK: {num_workers} workers for {num_chunks} chunks",
                    foreground="green",
                    font=('Arial', 9, 'bold')
                )
        
        def on_directory_selected():
            """Called when a directory is selected - enables localhost checkbox and loads config."""
            # Enable localhost checkbox now that directory is selected
            localhost_checkbox.config(state='normal')
            
            # Load original config into preview
            update_preview()
            
            # Check for mismatches
            check_and_display_mismatch()
        
        def select_chunks_dir_with_check():
            """Browse for chunks directory."""
            initial_dir = Path.cwd() / "split-out"
            directory = self._custom_ask_directory(
                title="Select Chunks Directory (Single-click to select)",
                initialdir=str(initial_dir) if initial_dir.exists() else None
            )
            if directory:
                dir_var.set(directory)
                on_directory_selected()
        
        browse_dir_button.config(command=select_chunks_dir_with_check)
        
        def select_config_file_with_check():
            """Browse for workers_filesrv.json file."""
            initial_dir = Path(__file__).resolve().parent.parent / "choreo"
            config_file = filedialog.askopenfilename(
                title="Select workers_filesrv.json configuration file",
                initialdir=str(initial_dir),
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if config_file:
                config_var.set(config_file)
                if dir_var.get():  # Only update if directory already selected
                    update_preview()
                    check_and_display_mismatch()
        
        browse_config_button.config(command=select_config_file_with_check)
        
        # Initialize preview with current config (if it exists)
        update_preview()
        
        # Button frame with Launch and Cancel
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_and_launch_distribution():
            """Save the current configuration and launch distribution."""
            chunks_dir = dir_var.get()
            config_file = config_var.get()
            
            # Step 1: Validate chunks directory
            if not chunks_dir:
                self._show_messagebox(
                    messagebox.showwarning,
                    "No Directory",
                    "Please select a chunks directory first.",
                    parent=dialog
                )
                return
            
            if not Path(chunks_dir).exists():
                self._show_messagebox(
                    messagebox.showerror,
                    "Invalid Directory",
                    f"Directory not found: {chunks_dir}",
                    parent=dialog
                )
                return
            
            # Step 2: Validate/generate config file path
            if not config_file:
                # If localhost mode is enabled, auto-generate and save config
                if use_localhost_var.get():
                    default_config_dir = Path(__file__).resolve().parent.parent / "choreo"
                    default_config_dir.mkdir(parents=True, exist_ok=True)
                    config_file = str(default_config_dir / "workers_filesrv.json")
                    config_var.set(config_file)
                else:
                    # Only show warning if not using localhost auto-config
                    self._show_messagebox(
                        messagebox.showwarning,
                        "No Config File",
                        "Please specify a workers_filesrv.json file location.",
                        parent=dialog
                    )
                    return
            
            # Step 3: Get current configuration from preview (which may have been edited)
            current_config = get_current_preview_config()
            
            if not current_config:
                self._show_messagebox(
                    messagebox.showwarning,
                    "No Workers",
                    "No workers configuration found.\n\n"
                    "Please enable localhost configuration or manually edit the preview.",
                    parent=dialog
                )
                return
            
            # Step 4: Validate we have enough workers
            chunks_dir_path = Path(chunks_dir)
            qasm_files = [f for f in chunks_dir_path.glob('*.qasm') if f.stem.isdigit()]
            
            if qasm_files:
                chunk_numbers = [int(f.stem) for f in qasm_files]
                num_chunks = max(chunk_numbers) + 1
            else:
                num_chunks = 0
            
            num_workers = len(current_config)
            
            if num_chunks > num_workers:
                self._show_messagebox(
                    messagebox.showerror,
                    "Insufficient Workers",
                    f"Error: You have {num_chunks} chunks but only {num_workers} worker(s).\n\n"
                    f"You need at least {num_chunks} workers to distribute all chunks.",
                    parent=dialog
                )
                return
            
            # Step 5: Confirm workers are running (if not using localhost)
            if not using_localhost:
                confirm = self._show_messagebox(
                    messagebox.askyesno,
                    "Confirm Workers Running",
                    f"⚠ Important: Make sure all {num_workers} worker(s) are running on their respective hosts!\n\n"
                    f"Workers should be listening on ports {', '.join(addr.split(':')[1] if ':' in addr else addr for addr in sorted(current_config.values())[:5])}{'...' if len(current_config) > 5 else ''}\n\n"
                    f"Click 'Yes' if workers are running and ready.\n"
                    f"Click 'No' to cancel and start workers first.",
                    parent=dialog,
                    icon='warning'
                )
                
                if not confirm:
                    return
            
            # Step 6: Save the configuration to disk
            try:
                with open(config_file, 'w') as f:
                    json.dump(current_config, f, indent=4)
                print(f"Saved workers configuration to: {config_file}")
            except Exception as e:
                self._show_messagebox(messagebox.showerror, "Save Error", f"Failed to save configuration:\n{e}", parent=dialog)
                return
            
            # Step 7: Close dialog and launch distribution dialog
            dialog.destroy()
            self._show_distribution_dialog(chunks_dir, config_file, current_config, using_localhost)
        
        ttk.Button(button_frame, text="Launch Distribution", 
                  command=save_and_launch_distribution).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _show_distribution_dialog(self, chunks_dir: str, config_file: str, worker_config: dict, localhost_mode: bool):
        """Show distribution dialog with integrated worker management and controller."""
        dist_dialog = tk.Toplevel(self.root)
        dist_dialog.title("Distribution - Controller & Workers")
        dist_dialog.geometry("1200x900")
        dist_dialog.transient(self.root)
        dist_dialog.grab_set()
        self._focus_window(dist_dialog)
        
        # Track worker processes and threads
        worker_processes = {}
        worker_threads = {}
        worker_running = {}
        
        # Create main paned window (vertical split - workers on top, controller on bottom)
        main_paned = ttk.PanedWindow(dist_dialog, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top panel: Workers (only if localhost mode)
        if localhost_mode:
            workers_frame = ttk.LabelFrame(main_paned, text="Local Workers", padding="5")
            main_paned.add(workers_frame, weight=1)
            
            worker_notebook = ttk.Notebook(workers_frame)
            worker_notebook.pack(fill=tk.BOTH, expand=True)
            
            # Create a tab for each worker
            worker_tabs = {}
            worker_outputs = {}
            worker_buttons = {}
            
            for worker_id in sorted(worker_config.keys(), key=lambda x: int(x)):
                address = worker_config[worker_id]
                if ':' not in address:
                    continue
                    
                host, port = address.rsplit(':', 1)
                port = int(port)
                
                # Only show localhost workers
                if host not in ('127.0.0.1', 'localhost'):
                    continue
                
                # Create tab for this worker
                tab_frame = ttk.Frame(worker_notebook)
                worker_notebook.add(tab_frame, text=f"Worker {worker_id} (:{port})")
                worker_tabs[worker_id] = tab_frame
                
                # Control buttons
                control_frame = ttk.Frame(tab_frame)
                control_frame.pack(fill=tk.X, padx=5, pady=5)
                
                start_btn = tk.Button(control_frame, text="▶ Start",
                                     command=lambda wid=worker_id, p=port: self._start_worker(wid, p, worker_outputs, worker_running, worker_threads, worker_buttons),
                                     bg='#4CAF50', fg='white',
                                     font=('Arial', 10, 'bold'), relief=tk.RAISED, bd=2,
                                     padx=10, pady=5, cursor='hand2')
                start_btn.pack(side=tk.LEFT, padx=2)
                
                stop_btn = ttk.Button(control_frame, text="⏹ Stop", state='disabled',
                                     command=lambda wid=worker_id: self._stop_worker(wid, worker_running, worker_threads, worker_buttons))
                stop_btn.pack(side=tk.LEFT, padx=2)
                
                worker_buttons[worker_id] = {'start': start_btn, 'stop': stop_btn}
                worker_running[worker_id] = False
                
                # Output text area with better width for long lines
                output_text = scrolledtext.ScrolledText(tab_frame, height=12, font=('Courier', 9), 
                                                       bg='#1e1e1e', fg='#d4d4d4', insertbackground='white',
                                                       wrap=tk.NONE)  # Don't wrap lines
                # Configure color tags for worker output
                output_text.tag_config('success', foreground='#4CAF50')  # Green
                output_text.tag_config('error', foreground='#FF6B6B')   # Red
                output_text.tag_config('warning', foreground='#FFA500') # Orange
                output_text.tag_config('normal', foreground='#d4d4d4')  # Default
                
                output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                output_text.insert('1.0', f"Worker {worker_id} on port {port}\nReady to start...\n")
                worker_outputs[worker_id] = output_text
        else:
            # No localhost mode - show message
            workers_frame = ttk.LabelFrame(main_paned, text="Workers (Disabled)", padding="5")
            main_paned.add(workers_frame, weight=1)
            
            msg_label = ttk.Label(workers_frame, 
                                 text="Worker management disabled.\n\n"
                                      "Workers must be started manually on their respective hosts.\n\n"
                                      "Use: python -m choreo.worker <port>",
                                 justify=tk.CENTER)
            msg_label.pack(expand=True)
        
        # Bottom panel: Controller
        controller_frame = ttk.LabelFrame(main_paned, text="Controller", padding="5")
        main_paned.add(controller_frame, weight=1)
        
        # Controller controls
        ctrl_control_frame = ttk.Frame(controller_frame)
        ctrl_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        distribute_btn = tk.Button(ctrl_control_frame, text="📤 Distribute Chunks",
                                  command=lambda: self._distribute_chunks(chunks_dir, config_file, controller_output),
                                  bg='#4CAF50', fg='white',
                                  font=('Arial', 10, 'bold'), relief=tk.RAISED, bd=2,
                                  padx=10, pady=5, cursor='hand2')
        distribute_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(ctrl_control_frame, text="Clear Output",
                              command=lambda: controller_output.delete('1.0', tk.END))
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Controller output with no line wrapping
        controller_output = scrolledtext.ScrolledText(controller_frame, height=12, font=('Courier', 9),
                                                     bg='#1e1e1e', fg='#d4d4d4', insertbackground='white',
                                                     wrap=tk.NONE)  # Don't wrap lines
        # Configure color tags for controller output
        controller_output.tag_config('success', foreground='#4CAF50')  # Green
        controller_output.tag_config('error', foreground='#FF6B6B')   # Red
        controller_output.tag_config('warning', foreground='#FFA500') # Orange
        controller_output.tag_config('normal', foreground='#d4d4d4')  # Default
        
        controller_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        controller_output.insert('1.0', f"Controller ready to distribute chunks from:\n{chunks_dir}\n\n"
                                       f"Using configuration: {config_file}\n"
                                       f"Workers: {len(worker_config)}\n\n"
                                       f"Click 'Distribute Chunks' to send files to workers.\n\n")
        
        # Bottom button frame
        bottom_frame = ttk.Frame(dist_dialog)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def on_close():
            """Clean up and close dialog."""
            # Stop all running workers
            if localhost_mode:
                for worker_id in list(worker_running.keys()):
                    if worker_running.get(worker_id, False):
                        self._stop_worker(worker_id, worker_running, worker_threads, worker_buttons)
            dist_dialog.destroy()
        
        ttk.Button(bottom_frame, text="Close", command=on_close).pack(side=tk.RIGHT, padx=5)
        
        # Handle window close button
        dist_dialog.protocol("WM_DELETE_WINDOW", on_close)
    
    def _start_worker(self, worker_id: str, port: int, worker_outputs: dict, 
                     worker_running: dict, worker_threads: dict, worker_buttons: dict):
        """Start a worker process in a thread."""
        from choreo.worker import Worker
        import queue
        
        if worker_running.get(worker_id, False):
            return
        
        output_widget = worker_outputs[worker_id]
        output_widget.insert(tk.END, f"\n[{self._timestamp()}] Starting worker on port {port}...\n")
        output_widget.see(tk.END)
        
        # Create output directory
        output_dir = Path.cwd() / "split-received"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Message queue for thread-safe output
        output_queue = queue.Queue()
        # Mark as running immediately so the poller keeps running from the start
        worker_running[worker_id] = True
        worker_threads[worker_id] = {'worker': None, 'queue': output_queue}
        
        def worker_thread():
            """Worker thread function."""
            try:
                # Inform user that output is ready
                output_queue.put("[System] Worker output capture started\n")

                def output_callback(msg: str) -> None:
                    output_queue.put(msg)

                worker = Worker(
                    port=port,
                    host="127.0.0.1",
                    output_dir=str(output_dir),
                    output_callback=output_callback,
                )
                worker_threads[worker_id] = {'worker': worker, 'queue': output_queue}
                
                worker.start()
                
            except Exception as e:
                output_queue.put(f"[ERROR] Worker exception: {e}\n")
            finally:
                worker_running[worker_id] = False
                output_queue.put(f"[System] Worker stopped.\n")
        
        # Start worker thread
        thread = threading.Thread(target=worker_thread, daemon=True)
        thread.start()
        
        # Update UI
        worker_buttons[worker_id]['start'].config(state='disabled')
        worker_buttons[worker_id]['stop'].config(state='normal')
        
        # Start output poller
        def poll_output():
            """Poll the output queue and update the text widget with colored output."""
            messages_processed = 0
            try:
                if not output_widget.winfo_exists():
                    return
                # Drain entire queue
                while True:
                    msg = output_queue.get_nowait()
                    if not msg:
                        continue
                    
                    messages_processed += 1
                    
                    # Determine tag based on message content
                    tag = 'normal'
                    msg_lower = msg.lower()
                    
                    # Check for success messages (green)
                    if any(x in msg_lower for x in ['✓', 'received', 'listening', 'success', 'sent', 'ready', 'waiting for files', 'output directory', 'capture started']):
                        tag = 'success'
                    # Check for error messages (red)
                    elif any(x in msg_lower for x in ['✗', 'failed', 'error', 'refused', 'cannot', 'exception']):
                        tag = 'error'
                    
                    output_widget.insert(tk.END, msg, tag)
                    output_widget.see(tk.END)
            except queue.Empty:
                pass
            except tk.TclError:
                # Widget was destroyed while polling
                return
            except Exception as e:
                print(f"Poll error: {e}")
            
            # Schedule next poll if worker is still running
            if output_widget.winfo_exists() and (worker_running.get(worker_id, False) or not output_queue.empty()):
                self.root.after(100, poll_output)
        
        self.root.after(100, poll_output)
    
    def _stop_worker(self, worker_id: str, worker_running: dict, worker_threads: dict, worker_buttons: dict):
        """Stop a worker process."""
        if not worker_running.get(worker_id, False):
            return
        
        worker_data = worker_threads.get(worker_id)
        if worker_data and 'worker' in worker_data:
            worker = worker_data['worker']
            worker.stop()
        
        worker_running[worker_id] = False
        
        # Update UI
        worker_buttons[worker_id]['start'].config(state='normal')
        worker_buttons[worker_id]['stop'].config(state='disabled')
    
    def _distribute_chunks(self, chunks_dir: str, config_file: str, output_widget: scrolledtext.ScrolledText):
        """Distribute chunks using the controller."""
        output_widget.insert(tk.END, f"\n{'='*60}\n")
        output_widget.insert(tk.END, f"[{self._timestamp()}] Starting distribution...\n")
        output_widget.insert(tk.END, f"{'='*60}\n")
        output_widget.see(tk.END)
        
        def distribute():
            """Run distribution in separate thread."""
            try:
                controller = Controller(Path(config_file))
                
                # Capture output
                import sys
                from io import StringIO
                
                old_stdout = sys.stdout
                output_buffer = StringIO()
                sys.stdout = output_buffer
                
                controller.distribute_files(chunks_dir)
                
                sys.stdout = old_stdout
                output = output_buffer.getvalue()
                
                # Update output widget
                self.root.after(0, lambda: self._append_controller_output(output_widget, output))
                
            except Exception as e:
                self.root.after(0, lambda: self._append_controller_output(
                    output_widget, f"Error during distribution:\n{str(e)}\n"))
        
        # Run in background thread
        thread = Thread(target=distribute, daemon=True)
        thread.start()
    
    def _append_controller_output(self, output_widget: scrolledtext.ScrolledText, text: str):
        """Append text to controller output widget with colored output based on keywords."""
        # Split text into lines and apply colors to each line
        for line in text.split('\n'):
            if not line:
                output_widget.insert(tk.END, '\n')
                continue
                
            # Determine tag based on line content - only color clear errors and successes
            tag = 'normal'
            if 'Error' in line or 'refused' in line.lower() or 'failed' in line.lower() or '✗' in line:
                tag = 'error'
            elif 'Success' in line or 'Sent' in line or 'completed' in line.lower() or '✓' in line:
                tag = 'success'
            
            output_widget.insert(tk.END, line + '\n', tag)
        
        # Add completion message in green
        output_widget.insert(tk.END, f"[{self._timestamp()}] Distribution completed.\n", 'success')
        output_widget.see(tk.END)
    
    def _timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def _run_controller_distribution(self, chunks_dir: str, config_file: str):
        """Run the controller distribution in a separate thread."""
        def distribute():
            try:
                controller = Controller(Path(config_file))
                
                # Capture output
                import io
                from contextlib import redirect_stdout
                
                output_buffer = io.StringIO()
                with redirect_stdout(output_buffer):
                    controller.distribute_files(chunks_dir)
                
                output = output_buffer.getvalue()
                
                # Show results in a new window
                self.root.after(0, lambda: self._show_distribution_results(output))
                
            except Exception as e:
                error_msg = f"Error during distribution:\n{str(e)}"
                self.root.after(0, lambda: self._show_messagebox(messagebox.showerror, "Distribution Error", error_msg))
        
        # Run in background thread
        thread = Thread(target=distribute, daemon=True)
        thread.start()
        
        # Show progress message
        self._show_status("Distributing chunks to workers...", blink=False)
    
    def _show_distribution_results(self, output: str):
        """Display the distribution results in a new window."""
        results_window = tk.Toplevel(self.root)
        results_window.title("Distribution Results")
        results_window.geometry("700x500")
        results_window.transient(self.root)
        self._focus_window(results_window)
        
        # Results text
        results_text = scrolledtext.ScrolledText(results_window, wrap=tk.WORD, font=('Courier', 9))
        results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        results_text.insert('1.0', output)
        results_text.config(state='disabled')
        
        # Close button
        ttk.Button(results_window, text="Close", 
                  command=results_window.destroy).pack(pady=10)
        
        self._show_status("Distribution completed!")
    
    def run(self):
        self.root.mainloop()
