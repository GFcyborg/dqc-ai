#!/usr/bin/env python3
"""
Standalone controller startup script.

This script distributes quantum circuit files to configured worker nodes.
Usage:
    python start_controller.py <input_dir> [--config workers_filesrv.json]

Example:
    python start_controller.py ./split-out --config workers_filesrv.json
"""

import sys
import os

# Add src/main/python to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.join(script_dir, 'src', 'main', 'python')
if os.path.exists(python_path):
    sys.path.insert(0, python_path)

from choreo import Controller
from pathlib import Path
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Start a controller node to distribute quantum circuits to workers"
    )
    parser.add_argument(
        "input_dir",
        help="Directory containing quantum circuit files to distribute"
    )
    parser.add_argument(
        "--config",
        default="workers_filesrv.json",
        help="Path to worker configuration file (default: workers_filesrv.json)"
    )
    
    args = parser.parse_args()
    
    config_file = Path(args.config)
    if not config_file.exists():
        print(f"Error: Configuration file not found: {config_file}")
        print("Create a workers_filesrv.json file with worker addresses, e.g.:")
        print('{')
        print('    "0": "localhost:6660",')
        print('    "1": "192.168.1.100:6661",')
        print('    "2": "192.168.1.101:6662"')
        print('}')
        sys.exit(1)
    
    print(f"Starting Choreo Controller")
    print(f"  Input directory: {args.input_dir}")
    print(f"  Config file: {config_file}")
    print()
    
    controller = Controller(config_file)
    controller.distribute_files(args.input_dir)


if __name__ == "__main__":
    main()
