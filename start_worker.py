#!/usr/bin/env python3
"""
Standalone worker startup script for remote hosts.

This script can be used to start a worker node on a remote host.
Usage:
    python start_worker.py <port> [--host 0.0.0.0] [--output-dir ./split-received]

Example:
    # Listen on all interfaces, port 6660
    python start_worker.py 6660
    
    # Listen on specific interface
    python start_worker.py 6660 --host 192.168.1.100
    
    # Custom output directory
    python start_worker.py 6660 --output-dir /data/quantum_chunks
"""

import sys
import os

# Add src/main/python to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.join(script_dir, 'src', 'main', 'python')
if os.path.exists(python_path):
    sys.path.insert(0, python_path)

from choreo import Worker
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Start a standalone worker node for distributed quantum circuit processing"
    )
    parser.add_argument("port", type=int, help="TCP port to listen on")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host/network interface to bind to (default: 0.0.0.0 for all interfaces)"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to save received files (default: ./split-received/)"
    )
    
    args = parser.parse_args()
    
    print(f"Starting Choreo Worker")
    print(f"  Port: {args.port}")
    print(f"  Host: {args.host}")
    print(f"  Output dir: {args.output_dir or './split-received/'}")
    print()
    
    worker = Worker(
        port=args.port,
        host=args.host,
        output_dir=args.output_dir
    )
    worker.start()


if __name__ == "__main__":
    main()
