#!/usr/bin/env python3
"""
Test script to verify the installation

This script tests the basic functionality without launching the GUI.
"""

import sys
import os

# Add src/main/python to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'main', 'python'))


def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from analyzer import VariableAnalyzer, VariableInfo
        print("✓ Analyzer module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import analyzer: {e}")
        return False
    
    try:
        from parser import QasmParser
        print("✓ Parser module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import parser: {e}")
        return False
    
    try:
        from gui import QasmAnalyzerGUI
        print("✓ GUI module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import GUI: {e}")
        return False
    
    return True


def test_analyzer():
    """Test the variable analyzer"""
    print("\nTesting Variable Analyzer...")
    
    from analyzer import VariableAnalyzer
    
    # Sample QASM code
    qasm_code = """OPENQASM 3.0;
qubit[2] q;
bit[2] c;

h q[0];
cx q[0], q[1];

c[0] = measure q[0];
c[1] = measure q[1];
"""
    
    try:
        analyzer = VariableAnalyzer()
        split_points = [5]  # Split after line 5
        chunks = analyzer.analyze(qasm_code, split_points)
        
        if len(chunks) != 2:
            print(f"✗ Expected 2 chunks, got {len(chunks)}")
            return False
        
        print(f"✓ Analyzed code into {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i}: lines {chunk.start_line}-{chunk.end_line-1}, "
                  f"{len(chunk.required_variables)} required variables")
        
        return True
    except Exception as e:
        print(f"✗ Analyzer test failed: {e}")
        return False


def test_parser():
    """Test the QASM parser"""
    print("\nTesting QASM Parser...")
    
    try:
        from parser import QasmParser
        
        parser = QasmParser()
        
        # Simple QASM code
        qasm_code = """OPENQASM 3.0;
qubit q;
bit c;
h q;
c = measure q;
"""
        
        result = parser.parse_string(qasm_code)
        
        if result.errors:
            print(f"✗ Parse errors: {result.errors}")
            return False
        
        if not result.ast:
            print("✗ No AST generated")
            return False
        
        print(f"✓ Successfully parsed QASM code")
        print(f"  AST type: {result.ast.get('type', 'unknown')}")
        
        return True
        
    except RuntimeError as e:
        print(f"⚠ Parser not available: {e}")
        print("  This is expected if you haven't run 'gradle generateGrammarSource' yet")
        print("  The analyzer will still work without AST display")
        return True  # Not a failure, just not set up yet
    except Exception as e:
        print(f"✗ Parser test failed with exception: {e}")
        return False


def main():
    print("=" * 60)
    print("DQC - OpenQASM Splitter - Installation Test")
    print("=" * 60)
    
    # Test imports
    if not test_imports():
        print("\n✗ Import test failed")
        return 1
    
    # Test analyzer (doesn't need ANTLR)
    try:
        if not test_analyzer():
            print("\n✗ Analyzer test failed")
            return 1
    except Exception as e:
        print(f"\n✗ Analyzer test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Test parser (needs ANTLR)
    try:
        if not test_parser():
            print("\n✗ Parser test failed")
            return 1
    except Exception as e:
        print(f"\n✗ Parser test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 60)
    print("✓ All installation tests passed!")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
