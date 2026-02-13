"""
Controller node for distributing quantum circuit files to worker nodes.

Usage (CLI):
    python -m choreo.controller <input_directory> [--output-config workers.json]

Usage (Python):
    from choreo import Controller
    controller = Controller(config_file)
    controller.distribute_files(input_dir)
"""

import json
import os
import socket
import sys
import argparse
from pathlib import Path
from typing import Dict
import time

from .protocol import FileTransferProtocol


class Controller:
    """Distributes quantum circuit files to worker nodes based on configuration."""
    
    def __init__(self, config_file: Path):
        """
        Initialize controller with worker configuration.
        
        Args:
            config_file: Path to workers.json mapping worker IDs to addresses
        """
        with open(config_file, 'r') as f:
            self.workers = json.load(f)
        self.config_file = config_file
    
    def distribute_files(self, input_dir: str) -> None:
        """
        Distribute files from input directory to workers according to mapping.
        
        Args:
            input_dir: Path to directory containing files to distribute
        
        Raises:
            ValueError: If the input directory is not valid
        """
        if not os.path.isdir(input_dir):
            raise ValueError(f"Directory '{input_dir}' not found")
        
        # Get list of .qasm files
        qasm_files = [f for f in os.listdir(input_dir) if f.endswith('.qasm')]
        
        if not qasm_files:
            print(f"Warning: No .qasm files found in '{input_dir}'")
            return
        
        print(f"Found {len(qasm_files)} .qasm files to distribute")
        print(f"Using {len(self.workers)} workers from configuration\n")
        
        # Distribute files
        for i, file_name in enumerate(sorted(qasm_files)):
            worker_id = str(i)
            if worker_id not in self.workers:
                print(f"Warning: No worker configured for ID {worker_id}, skipping {file_name}")
                continue
            
            worker_addr = self.workers[worker_id]
            file_path = os.path.join(input_dir, file_name)
            
            print(f"Sending '{file_name}' to worker {worker_id} ({worker_addr})...")
            self._send_file_to_worker(worker_addr, file_path, file_name)
    
    def _send_file_to_worker(self, worker_addr: str, file_path: str, file_name: str) -> None:
        """
        Send a file to a specific worker node.
        
        Args:
            worker_addr: Worker address in format "host:port"
            file_path: Full path to the file to send
            file_name: Name of the file (as seen by worker)
        """
        try:
            host, port = worker_addr.rsplit(':', 1)
            port = int(port)
        except (ValueError, IndexError):
            print(f"  Error: Invalid worker address format '{worker_addr}'")
            return
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(FileTransferProtocol.TIMEOUT)
            sock.connect((host, port))
            
            success = FileTransferProtocol.send_file(sock, file_path, file_name)
            
            if success:
                print(f"  ✓ File '{file_name}' sent successfully")
            else:
                print(f"  ✗ No acknowledgment from worker")
            
            sock.close()
            
        except socket.timeout:
            print(f"  ✗ Connection timeout (worker may not be running)")
        except ConnectionRefusedError:
            print(f"  ✗ Connection refused (worker not listening on {worker_addr})")
        except Exception as e:
            print(f"  ✗ Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Controller node for distributing quantum circuit files"
    )
    parser.add_argument("directory", help="Input directory containing files to distribute")
    parser.add_argument("--config", default=None, help="Worker configuration file (default: workers.json)")
    
    args = parser.parse_args()
    
    # Use config file from directory if not explicitly provided
    if args.config is not None:
        config_file = Path(args.config)
    else:
        config_file = Path(__file__).resolve().parent / "workers.json"
    
    if not config_file.exists():
        print(f"Error: workers configuration file not found: {config_file}")
        sys.exit(1)
    
    controller = Controller(config_file=config_file)
    controller.distribute_files(args.directory)


if __name__ == "__main__":
    main()
