"""
Main GUI window for DQC - OpenQASM Splitter
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from pathlib import Path
import requests
import re
from typing import Dict, List, Tuple

from parser import QasmParser
from analyzer import VariableAnalyzer
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
            messagebox.showerror("Parser Not Available",
                f"{e}\n\nYou can still use the variable analyzer without AST display.")
        
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
            messagebox.showerror("Download Error", f"Failed to download file:\n{e}")
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
            messagebox.showerror("File Error", f"Failed to load file:\n{e}")
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
            messagebox.showwarning("No Split Points", "Please mark at least one split point.")
            return
        
        if not self.current_file:
            messagebox.showwarning("No File", "Please load a file first.")
            return
        
        base_name, original_filename = self._get_filenames()
        split_out_root = Path.cwd() / "split-out"
        output_dir = split_out_root / base_name
        
        try:
            split_out_root.mkdir(parents=True, exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create output directory:\n{e}")
            return
        
        try:
            self._save_include_and_original_files(split_out_root, original_filename)
            self._save_dqc_with_pragmas(split_out_root, original_filename)
            self._save_chunks_to_files(output_dir, base_name)
            
            chunks_count = len(self.analyzer.analyze(self.source_code, list(self.split_points)))
            messagebox.showinfo("Success", f"Saved {chunks_count} chunks to:\n{output_dir}")
            self._show_status(f"Saved {chunks_count} chunks to {output_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save chunks:\n{e}")
    
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
    
    def run(self):
        self.root.mainloop()
