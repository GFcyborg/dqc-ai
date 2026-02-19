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
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

from .protocol import FileTransferProtocol


class Controller:
    """Distributes quantum circuit files to worker nodes based on configuration."""

    INCLUDE_PATTERN = re.compile(r'^\s*include\s+"([^"]+)"\s*;\s*$', re.IGNORECASE)
    
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
        input_dir_path = Path(input_dir).resolve()

        for i, file_name in enumerate(sorted(qasm_files)):
            worker_id = str(i)
            if worker_id not in self.workers:
                print(f"Warning: No worker configured for ID {worker_id}, skipping {file_name}")
                continue
            
            worker_addr = self.workers[worker_id]
            file_path = os.path.join(input_dir, file_name)
            
            print(f"Sending '{file_name}' to worker {worker_id} ({worker_addr})...")
            sent = self._send_file_to_worker(worker_addr, file_path, file_name)
            if sent:
                include_files = self._collect_include_files(file_path, input_dir_path)
                for include_name, include_path in include_files:
                    print(f"  Sending include '{include_name}' to worker {worker_id}...")
                    self._send_file_to_worker(worker_addr, str(include_path), include_name)
    
    def _send_file_to_worker(self, worker_addr: str, file_path: str, file_name: str) -> bool:
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
            return False
        
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
            return success
        except socket.timeout:
            print(f"  ✗ Connection timeout (worker may not be running)")
        except ConnectionRefusedError:
            print(f"  ✗ Connection refused (worker not listening on {worker_addr})")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        return False

    def _collect_include_files(self, file_path: str, input_dir_path: Path) -> List[Tuple[str, Path]]:
        """
        Parse include statements from a QASM file and resolve their paths.

        Args:
            file_path: Path to the QASM file being sent
            input_dir_path: Base directory used for distribution

        Returns:
            List of (include_name, include_path) pairs in file order.
        """
        include_names = self._extract_includes(file_path)
        resolved: List[Tuple[str, Path]] = []
        seen: set = set()

        for include_name in include_names:
            include_path = self._resolve_include_path(include_name, Path(file_path), input_dir_path)
            if include_path is None:
                print(f"  Warning: Include file '{include_name}' not found for '{Path(file_path).name}'")
                continue
            key = (include_name, str(include_path))
            if key in seen:
                continue
            seen.add(key)
            resolved.append((include_name, include_path))

        return resolved

    def _extract_includes(self, file_path: str) -> List[str]:
        """Extract include file names from a QASM file."""
        includes: List[str] = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    match = self.INCLUDE_PATTERN.match(line)
                    if match:
                        includes.append(match.group(1))
        except Exception as e:
            print(f"  Warning: Could not read includes from '{Path(file_path).name}': {e}")
        return includes

    def _resolve_include_path(
        self,
        include_name: str,
        qasm_path: Path,
        input_dir_path: Path,
    ) -> Optional[Path]:
        """Resolve include file path relative to the QASM file and its parent directories."""
        include_path = Path(include_name)
        if include_path.is_absolute() and include_path.exists():
            return include_path

        search_root = input_dir_path.parent if input_dir_path.parent else input_dir_path
        for candidate_dir in [qasm_path.parent, *qasm_path.parent.parents]:
            candidate = candidate_dir / include_path
            if candidate.exists():
                return candidate
            if candidate_dir == search_root:
                break

        return None


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
