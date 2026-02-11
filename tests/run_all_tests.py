#!/usr/bin/env python3
"""
Main test runner for DQC - OpenQASM Splitter

Runs all test suites and provides a summary report.
"""

import sys
import os
import subprocess
from pathlib import Path

# Get the tests directory relative to this script's location
TESTS_DIR = str(Path(__file__).parent)
PROJECT_DIR = str(Path(__file__).parent.parent)


def run_test(test_name, test_path):
    """Run a single test file and return whether it passed"""
    print(f"\n{'=' * 60}")
    print(f"Running: {test_name}")
    print('=' * 60)
    
    try:
        result = subprocess.run(
            [sys.executable, test_path],
            cwd=PROJECT_DIR,
            capture_output=False,
            text=True,
            timeout=60
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"✗ {test_name} timed out")
        return False
    except Exception as e:
        print(f"✗ Failed to run {test_name}: {e}")
        return False


def main():
    print("=" * 60)
    print("DQC - OpenQASM Splitter - Test Suite")
    print("=" * 60)
    
    # Discover and run tests
    test_files = [
        ('Installation Tests', os.path.join(TESTS_DIR, 'test_installation.py')),
        ('GUI Enhancement Tests', os.path.join(TESTS_DIR, 'test_gui_enhancements.py')),
        ('DQC Grammar Tests', os.path.join(TESTS_DIR, 'test_dqc_grammar.py')),
        ('DQC Wrapper Tests', os.path.join(TESTS_DIR, 'test_dqc_wrapper.py')),
        ('Include Download Tests', os.path.join(TESTS_DIR, 'test_include_download.py')),
        ('Include Extraction Tests', os.path.join(TESTS_DIR, 'test_includes.py')),
        ('Include Save Tests', os.path.join(TESTS_DIR, 'test_save_includes.py')),
        ('Include Tabs Tests', os.path.join(TESTS_DIR, 'test_include_tabs.py')),
    ]
    
    results = {}
    for test_name, test_path in test_files:
        if os.path.exists(test_path):
            results[test_name] = run_test(test_name, test_path)
        else:
            print(f"\n! Test file not found: {test_path}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_flag in results.items():
        status = "✓ PASSED" if passed_flag else "✗ FAILED"
        print(f"{test_name:40} {status}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} test suites passed")
    print("=" * 60)
    
    if passed == total:
        print("\n✓ All tests passed! The application is ready to use.")
        print("\nTo start the GUI:")
        print("  ./run.sh")
        print("  or")
        print("  source .venv/bin/activate && python3 main.py")
        return 0
    else:
        print(f"\n✗ {total - passed} test suite(s) failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
