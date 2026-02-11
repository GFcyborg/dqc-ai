#!/usr/bin/env python3
"""Integration test for include file handling in GUI"""

import sys
import os
from pathlib import Path
import tkinter as tk

PROJECT_DIR = Path(__file__).resolve().parents[1]

# Add src to path
sys.path.insert(0, str(PROJECT_DIR / 'src' / 'main' / 'python'))

from gui.main_window import QasmAnalyzerGUI

def test_include_tabs():
    """Test that include tabs are created when loading a file with includes"""
    
    print("Integration Test: Including library files in GUI tabs\n")
    
    # Create a dummy GUI instance
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    # Create GUI
    gui = QasmAnalyzerGUI(root)
    print("✓ GUI created successfully")
    
    # Load the adder.qasm file which has include "stdgates.inc"
    adder_file = PROJECT_DIR / "split-out" / "adder.qasm"
    
    if adder_file.exists():
        print(f"✓ Found test file: {adder_file}")
        
        # Load the file
        gui._load_file(str(adder_file))
        print("✓ File loaded")
        
        # Check if includes were extracted
        includes = QasmAnalyzerGUI._extract_includes(gui.source_code)
        print(f"✓ Includes found: {includes}")
        
        # Check if tabs were created
        if gui.include_tabs:
            print(f"✓ Include tabs created: {list(gui.include_tabs.keys())}")
            for filename, frame in gui.include_tabs.items():
                print(f"  - {filename}: Tab registered")
        else:
            print("✗ No include tabs were created")
        
        # Verify stdgates.inc content
        if "stdgates.inc" in gui.include_files:
            content = gui.include_files["stdgates.inc"]
            print(f"✓ stdgates.inc loaded ({len(content)} bytes)")
            if "gate u3" in content:
                print("  ✓ Contains gate definitions")
            else:
                print("  ✗ Gate definitions not found")
        else:
            print("✗ stdgates.inc not in include_files")
    else:
        print(f"✗ Test file not found: {adder_file}")
    
    # Clean up
    root.destroy()
    
    print("\n✓ Integration test completed!")

if __name__ == "__main__":
    test_include_tabs()
