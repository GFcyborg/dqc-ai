#!/usr/bin/env python3
"""Test script for include file extraction and downloading"""

import sys
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]

# Add src to path
sys.path.insert(0, str(PROJECT_DIR / 'src' / 'main' / 'python'))

from gui.main_window import QasmAnalyzerGUI

def test_extract_includes():
    """Test extracting include directives from QASM content"""
    
    test_cases = [
        ('include "stdgates.inc";', ['stdgates.inc']),
        ('include \'stdgates.inc\';', ['stdgates.inc']),
        ('include "stdgates.inc";\ninclude "custom.inc";', ['stdgates.inc', 'custom.inc']),
        ('INCLUDE "stdgates.inc";', ['stdgates.inc']),  # Case insensitive
        ('  include  "stdgates.inc"  ;', ['stdgates.inc']),  # Extra whitespace
        ('// include "not_included.inc";\ninclude "real.inc";', ['real.inc']),  # Commented out
        ('no includes here', []),  # No includes
    ]
    
    print("Testing include extraction:\n")
    for content, expected in test_cases:
        result = QasmAnalyzerGUI._extract_includes(content)
        status = "✓" if result == expected else "✗"
        print(f"{status} Content: {repr(content[:40])}")
        if result != expected:
            print(f"  Expected: {expected}, Got: {result}")
        else:
            print(f"  Result: {result}")
        print()

def test_actual_qasm_file():
    """Test on actual QASM file"""
    
    adder_file = PROJECT_DIR / "split-out" / "adder.qasm"
    
    if adder_file.exists():
        print(f"Testing with actual file: {adder_file}")
        with open(adder_file, 'r') as f:
            content = f.read()
        
        includes = QasmAnalyzerGUI._extract_includes(content)
        print(f"Includes found: {includes}\n")
    else:
        print(f"Adder file not found at {adder_file}\n")

if __name__ == "__main__":
    test_extract_includes()
    test_actual_qasm_file()
    
    print("All tests completed!")
