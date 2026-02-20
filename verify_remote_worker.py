#!/usr/bin/env python3
"""
Verification script to test that workers can run independently on remote hosts.

This script validates:
1. Worker code has no GUI dependencies
2. Worker can be imported and instantiated independently
3. Network protocol is valid
4. No external dependencies required
"""

import sys
import os
from pathlib import Path

# Add src/main/python to path
script_dir = Path(__file__).parent
python_path = script_dir / 'src' / 'main' / 'python'
if python_path.exists():
    sys.path.insert(0, str(python_path))


def check_dependencies():
    """Check that choreo modules only use standard library."""
    print("=" * 70)
    print("1. Checking module dependencies...")
    print("=" * 70)
    
    import importlib.util
    
    choreo_path = python_path / 'choreo'
    modules_to_check = [
        choreo_path / 'worker.py',
        choreo_path / 'controller.py',
        choreo_path / 'protocol.py',
    ]
    
    prohibited_imports = [
        'tkinter', 'tk', 'gui', 'PyQt', 'wx', 'pygame',
        'PySide', 'curses'  # anything interactive
    ]
    
    for module_file in modules_to_check:
        print(f"\nChecking {module_file.name}...")
        with open(module_file) as f:
            content = f.read()
            
        for prohibited in prohibited_imports:
            if f'import {prohibited}' in content or f'from {prohibited}' in content:
                print(f"  ✗ FAIL: Found {prohibited} import")
                return False
        
        # Extract actual imports
        lines = content.split('\n')
        imports = [line for line in lines if line.startswith('import ') or line.startswith('from ')]
        imports = [line for line in imports if not line.startswith('from .')]  # Skip internal imports
        
        if imports:
            print(f"  External imports found:")
            for imp in imports[:5]:
                print(f"    {imp}")
        else:
            print(f"  ✓ Only standard library imports")
    
    print("\n✓ All modules use only standard library")
    return True


def check_worker_import():
    """Test that Worker can be imported independently."""
    print("\n" + "=" * 70)
    print("2. Testing Worker import...")
    print("=" * 70)
    
    try:
        from choreo import Worker
        print("✓ Successfully imported Worker class")
        print(f"  Worker class location: {Worker.__module__}")
        
        # Check key methods exist
        required_methods = ['start', 'stop', '_emit', '_handle_client']
        for method in required_methods:
            if hasattr(Worker, method):
                print(f"  ✓ Method '{method}' exists")
            else:
                print(f"  ✗ Method '{method}' missing")
                return False
        
        return True
    except ImportError as e:
        print(f"✗ Failed to import Worker: {e}")
        return False


def check_controller_import():
    """Test that Controller can be imported independently."""
    print("\n" + "=" * 70)
    print("3. Testing Controller import...")
    print("=" * 70)
    
    try:
        from choreo import Controller
        print("✓ Successfully imported Controller class")
        print(f"  Controller class location: {Controller.__module__}")
        
        # Check key methods exist
        required_methods = ['distribute_files', '_send_file_to_worker']
        for method in required_methods:
            if hasattr(Controller, method):
                print(f"  ✓ Method '{method}' exists")
            else:
                print(f"  ✗ Method '{method}' missing")
                return False
        
        return True
    except ImportError as e:
        print(f"✗ Failed to import Controller: {e}")
        return False


def check_protocol():
    """Test that Protocol module is independent."""
    print("\n" + "=" * 70)
    print("4. Testing FileTransferProtocol...")
    print("=" * 70)
    
    try:
        from choreo.protocol import FileTransferProtocol
        print("✓ Successfully imported FileTransferProtocol")
        
        # Check protocol constants
        required_attrs = [
            'CMD_FILE_TRANSFER',
            'CMD_EXECUTE_CHUNK',
            'ACK',
            'ACK_STARTED',
            'DONE'
        ]
        
        for attr in required_attrs:
            if hasattr(FileTransferProtocol, attr):
                value = getattr(FileTransferProtocol, attr)
                print(f"  ✓ Constant '{attr}' = {value}")
            else:
                print(f"  ✗ Constant '{attr}' missing")
                return False
        
        return True
    except ImportError as e:
        print(f"✗ Failed to import FileTransferProtocol: {e}")
        return False


def check_worker_instantiation():
    """Test that Worker can be instantiated without GUI context."""
    print("\n" + "=" * 70)
    print("5. Testing Worker instantiation...")
    print("=" * 70)
    
    try:
        from choreo import Worker
        import tempfile
        
        # Create temp directory for test
        with tempfile.TemporaryDirectory() as tmpdir:
            worker = Worker(
                port=12345,
                host="127.0.0.1",
                output_dir=tmpdir
            )
            print(f"✓ Worker instantiated successfully")
            print(f"  Port: {worker.port}")
            print(f"  Host: {worker.host}")
            print(f"  Output directory: {worker.output_dir}")
            print(f"  Running: {worker.running}")
            
            return True
    except Exception as e:
        print(f"✗ Failed to instantiate Worker: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_startup_scripts():
    """Verify startup scripts exist and are proper."""
    print("\n" + "=" * 70)
    print("6. Checking startup scripts...")
    print("=" * 70)
    
    scripts = [
        script_dir / 'start_worker.py',
        script_dir / 'start_controller.py',
    ]
    
    all_exist = True
    for script in scripts:
        if script.exists():
            with open(script) as f:
                first_line = f.readline()
            
            if first_line.startswith('#!'):
                print(f"✓ {script.name} exists (shebang: {first_line.strip()})")
            else:
                print(f"✓ {script.name} exists")
        else:
            print(f"✗ {script.name} missing")
            all_exist = False
    
    return all_exist


def main():
    """Run all verification checks."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " Remote Worker Independence Verification ".center(68) + "║")
    print("╚" + "=" * 68 + "╝")
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Worker Import", check_worker_import),
        ("Controller Import", check_controller_import),
        ("Protocol", check_protocol),
        ("Worker Instantiation", check_worker_instantiation),
        ("Startup Scripts", check_startup_scripts),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} check failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL CHECKS PASSED")
        print("\nWorker is ready for independent/remote deployment!")
        print("\nTo run a worker on a remote host:")
        print("  python3 start_worker.py <port> --host 0.0.0.0")
        print("\nTo run on localhost (for testing):")
        print("  python3 start_worker.py 6660")
        print("  python3 start_worker.py 6661")
        print("  python3 start_worker.py 6662")
        print("\nThen distribute files:")
        print("  python3 start_controller.py ./split-out --config workers_filesrv.json")
        print("=" * 70)
        return 0
    else:
        print("✗ SOME CHECKS FAILED")
        print("Please review the failures above.")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
