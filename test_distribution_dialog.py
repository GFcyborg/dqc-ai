#!/usr/bin/env python3
"""
Test script for the distribution dialog functionality.
Tests the worker management and controller UI logic without requiring ANTLR.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import sys
from pathlib import Path

# Add src/main/python to path
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'main' / 'python'))

def test_distribution_dialog():
    """Create a test window with the distribution dialog."""
    
    root = tk.Tk()
    root.title("Distribution Dialog Test")
    root.geometry("900x700")
    
    # Mock worker configuration
    worker_config = {
        "0": "127.0.0.1:6660",
        "1": "127.0.0.1:6661",
        "2": "127.0.0.1:6662"
    }
    
    chunks_dir = "./split-out/test"
    config_file = "./src/main/python/choreo/workers.json"
    localhost_mode = True
    
    # Track worker processes and threads
    worker_processes = {}
    worker_threads = {}
    worker_running = {}
    
    # Create main paned window (horizontal split)
    main_paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Left panel: Workers
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
            
            start_btn = ttk.Button(control_frame, text="▶ Start")
            start_btn.pack(side=tk.LEFT, padx=2)
            
            stop_btn = ttk.Button(control_frame, text="⏹ Stop", state='disabled')
            stop_btn.pack(side=tk.LEFT, padx=2)
            
            worker_buttons[worker_id] = {'start': start_btn, 'stop': stop_btn}
            worker_running[worker_id] = False
            
            # Output text area
            output_text = scrolledtext.ScrolledText(tab_frame, height=20, font=('Courier', 9), 
                                                   bg='#1e1e1e', fg='#d4d4d4', insertbackground='white')
            output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            output_text.insert('1.0', f"Worker {worker_id} on port {port}\nReady to start...\n")
            worker_outputs[worker_id] = output_text
    
    # Right panel: Controller
    controller_frame = ttk.LabelFrame(main_paned, text="Controller", padding="5")
    main_paned.add(controller_frame, weight=1)
    
    # Controller controls
    ctrl_control_frame = ttk.Frame(controller_frame)
    ctrl_control_frame.pack(fill=tk.X, padx=5, pady=5)
    
    def mock_distribute():
        controller_output.insert(tk.END, "\n" + "="*60 + "\n")
        controller_output.insert(tk.END, "Mock distribution started...\n")
        controller_output.insert(tk.END, "="*60 + "\n")
        controller_output.see(tk.END)
    
    distribute_btn = ttk.Button(ctrl_control_frame, text="📤 Distribute Chunks",
                               command=mock_distribute)
    distribute_btn.pack(side=tk.LEFT, padx=5)
    
    clear_btn = ttk.Button(ctrl_control_frame, text="Clear Output",
                          command=lambda: controller_output.delete('1.0', tk.END))
    clear_btn.pack(side=tk.LEFT, padx=5)
    
    # Controller output
    controller_output = scrolledtext.ScrolledText(controller_frame, height=20, font=('Courier', 9),
                                                 bg='#1e1e1e', fg='#d4d4d4', insertbackground='white')
    controller_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    controller_output.insert('1.0', f"Controller ready to distribute chunks from:\n{chunks_dir}\n\n"
                                   f"Using configuration: {config_file}\n"
                                   f"Workers: {len(worker_config)}\n\n"
                                   f"Click 'Distribute Chunks' to send files to workers.\n\n")
    
    # Bottom button frame
    bottom_frame = ttk.Frame(root)
    bottom_frame.pack(fill=tk.X, padx=10, pady=10)
    
    ttk.Button(bottom_frame, text="Close", command=root.destroy).pack(side=tk.RIGHT, padx=5)
    
    print("✓ Distribution dialog UI test loaded successfully")
    print("✓ Worker tabs created:", len(worker_tabs))
    print("✓ Controller panel initialized")
    print("\nClose the window when done testing.")
    
    root.mainloop()

if __name__ == "__main__":
    test_distribution_dialog()
