#!/usr/bin/env python3
"""
Test script for the localhost checkbox behavior with editable/non-editable JSON preview.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import json

def test_localhost_checkbox():
    """Test the localhost checkbox toggle behavior."""
    
    root = tk.Tk()
    root.title("Localhost Checkbox Test")
    root.geometry("600x500")
    
    # Mock configuration
    original_config = {
        "0": "192.168.1.10:6660",
        "1": "192.168.1.11:6660"
    }
    
    localhost_config = {
        "0": "127.0.0.1:6660",
        "1": "127.0.0.1:6661",
        "2": "127.0.0.1:6662"
    }
    
    # Localhost checkbox
    localhost_frame = ttk.LabelFrame(root, text="Localhost Configuration", padding="10")
    localhost_frame.pack(fill=tk.X, padx=10, pady=10)
    
    use_localhost_var = tk.BooleanVar(value=False)
    localhost_checkbox = ttk.Checkbutton(
        localhost_frame,
        text="Use localhost as worker nodes",
        variable=use_localhost_var
    )
    localhost_checkbox.pack(anchor=tk.W)
    
    # Status label
    status_label = tk.Label(root, text="Configuration is editable", 
                           font=('Arial', 9, 'italic'), foreground='gray')
    status_label.pack(fill=tk.X, padx=10, pady=5)
    
    # Preview frame
    preview_frame = ttk.LabelFrame(root, text="Configuration Preview", padding="10")
    preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    preview_text = scrolledtext.ScrolledText(preview_frame, height=10, font=('Courier', 9))
    preview_text.pack(fill=tk.BOTH, expand=True)
    preview_text.insert('1.0', json.dumps(original_config, indent=2))
    
    def on_localhost_toggle():
        """Handle localhost checkbox toggle."""
        if use_localhost_var.get():
            # Show localhost config and disable editing
            preview_text.config(state='normal')  # Temporarily enable to update content
            preview_text.delete('1.0', tk.END)
            preview_text.insert('1.0', json.dumps(localhost_config, indent=2))
            preview_text.config(state='disabled', bg='#e0e0e0')
            
            status_label.config(
                text="✓ Generated 3 localhost workers (configuration locked)",
                foreground='green',
                font=('Arial', 9, 'bold')
            )
        else:
            # Revert to original config and enable editing
            preview_text.config(state='normal', bg='white')
            preview_text.delete('1.0', tk.END)
            preview_text.insert('1.0', json.dumps(original_config, indent=2))
            
            status_label.config(
                text="Using configuration from file (editable)",
                foreground='gray',
                font=('Arial', 9, 'italic')
            )
    
    use_localhost_var.trace('w', lambda *args: on_localhost_toggle())
    
    # Test button to verify we can still read from disabled widget
    def test_read():
        """Test reading from the preview widget."""
        content = preview_text.get('1.0', tk.END).strip()
        config = json.loads(content)
        state = preview_text.cget('state')
        bg = preview_text.cget('bg')
        
        result = f"Widget State: {state}\n"
        result += f"Background Color: {bg}\n"
        result += f"Can Read: Yes\n"
        result += f"Workers: {len(config)}\n"
        result += f"Config: {json.dumps(config, indent=2)}"
        
        result_window = tk.Toplevel(root)
        result_window.title("Read Test Result")
        result_window.geometry("400x300")
        
        result_text = scrolledtext.ScrolledText(result_window, font=('Courier', 9))
        result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        result_text.insert('1.0', result)
    
    test_frame = ttk.Frame(root)
    test_frame.pack(fill=tk.X, padx=10, pady=10)
    
    ttk.Button(test_frame, text="Test Read from Preview", command=test_read).pack(side=tk.LEFT, padx=5)
    ttk.Button(test_frame, text="Close", command=root.destroy).pack(side=tk.RIGHT, padx=5)
    
    print("✓ Test UI loaded")
    print("✓ Toggle the checkbox to see editable/non-editable behavior")
    print("✓ Click 'Test Read' to verify programmatic reading works in both states")
    
    root.mainloop()

if __name__ == "__main__":
    test_localhost_checkbox()
