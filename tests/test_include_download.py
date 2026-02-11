#!/usr/bin/env python3
"""Test include file downloading"""

import sys
import os
import tempfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]

# Add src to path
sys.path.insert(0, str(PROJECT_DIR / 'src' / 'main' / 'python'))

from gui.main_window import QasmAnalyzerGUI
import tkinter as tk

def test_download_stdgates():
    """Test downloading the stdgates.inc file"""
    
    print("Testing stdgates.inc download...\n")
    
    # Create a dummy GUI instance just to use its methods
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        gui = QasmAnalyzerGUI(root)
        
        # Try to download stdgates.inc
        success, content = gui._download_include_file("stdgates.inc")
        
        if success:
            print("✓ Successfully downloaded stdgates.inc")
            print(f"  File size: {len(content)} bytes")
            print(f"  First 200 characters:\n{content[:200]}\n")
        else:
            print("✗ Failed to download stdgates.inc")
            print(f"  Error: {content}\n")
        
        root.destroy()
        
    except Exception as e:
        print(f"✗ Error during test: {e}")
        root.destroy()

if __name__ == "__main__":
    test_download_stdgates()
    print("Download test completed!")
