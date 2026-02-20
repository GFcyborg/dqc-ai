"""
Worker node for receiving and processing quantum circuit files.

Usage (CLI):
    python -m choreo.worker <port> [--host 0.0.0.0] [--output-dir ./split-received]

Usage (Python):
    from choreo import Worker
    worker = Worker(port=6660, output_dir="./split-received")
    worker.start()
"""

import socket
import sys
import argparse
import os
import threading
from pathlib import Path
from typing import Optional, Callable

from .protocol import FileTransferProtocol


class Worker:
    """Receives and processes quantum circuit files from controller."""
    
    def __init__(
        self,
        port: int,
        host: str = "0.0.0.0",
        output_dir: Optional[str] = None,
        output_callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize worker node.
        
        Args:
            port: TCP port to listen on
            host: Host/network interface to bind to (default: 0.0.0.0 for all interfaces)
            output_dir: Directory to save received files (default: ./split-received/)
        """
        self.port = port
        self.host = host
        self.output_dir = output_dir or "./split-received"
        
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        self.output_callback = output_callback
        self.running = False
        self.server_socket = None

    def _emit(self, message: str) -> None:
        if not message.endswith("\n"):
            message = message + "\n"
        if self.output_callback:
            self.output_callback(message)
        else:
            print(message, end="")
    
    def start(self) -> None:
        """Start the worker server."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            self._emit(f"Worker listening on {self.host}:{self.port}")
            self._emit(f"Output directory: {os.path.abspath(self.output_dir)}")
            self._emit("Waiting for files from controller...")
            
            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    if self.running:
                        self._emit(f"Error accepting connection: {e}")
        
        except OSError as e:
            self._emit(f"Error: Cannot bind to {self.host}:{self.port}")
            self._emit(f"Details: {e}")
            sys.exit(1)
        
        finally:
            self.stop()
    
    def _handle_client(self, client_socket: socket.socket, client_addr: tuple) -> None:
        """
        Handle incoming request from controller (file transfer or execution command).
        
        Args:
            client_socket: Socket connection from client
            client_addr: Client address (host, port)
        """
        try:
            # Read command byte to determine request type
            self._emit(f"[{client_addr[0]}:{client_addr[1]}] New connection, waiting for command byte...")
            cmd_byte = client_socket.recv(1)
            if not cmd_byte:
                self._emit(f"[{client_addr[0]}:{client_addr[1]}] No data received (connection closed)")
                return
            
            self._emit(f"[{client_addr[0]}:{client_addr[1]}] Command byte received: {cmd_byte.hex()}")
            
            if cmd_byte == FileTransferProtocol.CMD_FILE_TRANSFER:
                # Handle file transfer
                self._emit(f"[{client_addr[0]}:{client_addr[1]}] Processing file transfer...")
                success, output_path = FileTransferProtocol.receive_file(client_socket, self.output_dir)
                
                if success and output_path:
                    file_size = os.path.getsize(output_path)
                    file_name = os.path.basename(output_path)
                    self._emit(
                        f"[{client_addr[0]}:{client_addr[1]}] ✓ File '{file_name}' received successfully ({file_size} bytes)"
                    )
                else:
                    self._emit(f"[{client_addr[0]}:{client_addr[1]}] ✗ Failed to receive file")
            
            elif cmd_byte == FileTransferProtocol.CMD_EXECUTE_CHUNK:
                # Handle execution command
                self._emit(f"[{client_addr[0]}:{client_addr[1]}] Processing execution command...")
                self._emit(f"[{client_addr[0]}:{client_addr[1]}] Reading chunk ID...")
                chunk_id = FileTransferProtocol.receive_execute_command(client_socket)
                
                if chunk_id is not None:
                    self._emit(f"[{client_addr[0]}:{client_addr[1]}] ▶ Execution command received for chunk {chunk_id}")
                    
                    # Send ACK_STARTED
                    try:
                        self._emit(f"Sending ACK_STARTED ({len(FileTransferProtocol.ACK_STARTED)} bytes)...")
                        client_socket.sendall(FileTransferProtocol.ACK_STARTED)
                        self._emit(f"✓ ACK_STARTED sent")
                        self._emit(f"Acknowledged execution start for chunk {chunk_id}")
                    except Exception as e:
                        self._emit(f"✗ Error sending ACK_STARTED: {type(e).__name__}: {e}")
                        return
                    
                    # Execute the chunk (simulation)
                    try:
                        self._execute_chunk_simulation(chunk_id)
                    except Exception as e:
                        self._emit(f"✗ Error during simulation: {type(e).__name__}: {e}")
                    
                    # Send DONE
                    try:
                        self._emit(f"Sending DONE ({len(FileTransferProtocol.DONE)} bytes)...")
                        client_socket.sendall(FileTransferProtocol.DONE)
                        self._emit(f"✓ DONE sent")
                        self._emit(f"✓ Chunk {chunk_id} execution completed")
                    except Exception as e:
                        self._emit(f"✗ Error sending DONE: {type(e).__name__}: {e}")
                else:
                    self._emit(f"[{client_addr[0]}:{client_addr[1]}] ✗ Failed to receive chunk ID")
            else:
                self._emit(f"[{client_addr[0]}:{client_addr[1]}] ✗ Unknown command byte: {cmd_byte.hex()}")
        
        except Exception as e:
            self._emit(f"[{client_addr[0]}:{client_addr[1]}] Error: {type(e).__name__}: {e}")
        
        finally:
            client_socket.close()
    
    def _execute_chunk_simulation(self, chunk_id: str) -> None:
        """
        Simulate execution of a QASM chunk by analyzing its content.
        
        Args:
            chunk_id: ID of the chunk to execute (e.g., "0", "1", "2")
        """
        import re
        import time
        
        sys.stderr.write(f"[WORKER-EXEC] Starting simulation for chunk {chunk_id}\n")
        sys.stderr.flush()
        
        # Find the chunk file
        chunk_file = os.path.join(self.output_dir, f"{chunk_id}.qasm")
        
        sys.stderr.write(f"[WORKER-EXEC] Looking for chunk file: {chunk_file}\n")
        sys.stderr.write(f"[WORKER-EXEC] Output dir exists: {os.path.exists(self.output_dir)}\n")
        sys.stderr.write(f"[WORKER-EXEC] Files in output dir: {os.listdir(self.output_dir)}\n")
        sys.stderr.write(f"[WORKER-EXEC] Chunk file exists: {os.path.exists(chunk_file)}\n")
        sys.stderr.flush()
        
        if not os.path.exists(chunk_file):
            self._emit(f"  ✗ Error: Chunk file '{chunk_id}.qasm' not found in {self.output_dir}")
            return
        
        self._emit(f"  Simulating execution of chunk '{chunk_id}.qasm'...")
        
        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sys.stderr.write(f"[WORKER-EXEC] Read file, length: {len(content)} bytes\n")
            sys.stderr.flush()
            
            # ===== REQUIRED VARIABLES (from comments) =====
            # Extract "Required variables:" section for continuation chunks
            required_vars = []
            lines = content.split('\n')
            in_required_section = False
            
            for line in lines:
                stripped = line.strip()
                
                # Check if we're entering the required variables section
                if 'Required variables:' in line:
                    in_required_section = True
                    sys.stderr.write(f"[WORKER-EXEC] Found required variables section\n")
                    sys.stderr.flush()
                    continue
                
                # Stop reading required section when we hit a non-comment line or actual code
                if in_required_section:
                    if not stripped.startswith('//'):
                        in_required_section = False
                    elif stripped == '//':
                        # Empty comment line, skip
                        continue
                    else:
                        # Extract the variable descriptor (e.g., "gate majority" or "qubit[4] a")
                        # Remove the "//" and any leading/trailing whitespace
                        var_line = stripped[2:].strip()  # Remove "//"
                        if var_line and var_line not in ('Required variables:',):
                            required_vars.append(var_line)
                            sys.stderr.write(f"[WORKER-EXEC] Found required var: {var_line}\n")
                            sys.stderr.flush()
            
            sys.stderr.write(f"[WORKER-EXEC] Total required vars found in comments: {len(required_vars)}\n")
            sys.stderr.flush()
            
            # ===== DECLARED VARIABLES =====
            declared_quantum = []  # qubit, qubit[]
            declared_classical = []  # bit, bit[], int, float, angle, bool, complex
            declared_gates = []  # gate declarations
            includes = []
            
            # Extract include statements
            include_pattern = re.compile(r'^\s*include\s+"([^"]+)"\s*;', re.MULTILINE | re.IGNORECASE)
            includes = include_pattern.findall(content)
            
            # Extract gate declarations: gate <name> ...
            gate_pattern = re.compile(r'^\s*gate\s+(\w+)', re.MULTILINE | re.IGNORECASE)
            declared_gates = gate_pattern.findall(content)
            
            # Extract qubit declarations: qubit <name> or qubit[n] <name>
            qubit_pattern = re.compile(r'^\s*qubit(?:\s*\[\s*\d+\s*\])?\s+(\w+)', re.MULTILINE | re.IGNORECASE)
            declared_quantum = qubit_pattern.findall(content)
            
            # Extract classical variable declarations: bit, int, float, angle, bool, complex
            # Includes arrays: bit[n] <name>, int[n] <name>, etc.
            classical_pattern = re.compile(r'^\s*(?:bit|int|float|angle|bool|complex)(?:\s*\[\s*\d+\s*\])?\s+(\w+)', re.MULTILINE | re.IGNORECASE)
            declared_classical = classical_pattern.findall(content)
            
            sys.stderr.write(f"[WORKER-EXEC] Declarations - gates: {len(declared_gates)}, quantum: {len(declared_quantum)}, classical: {len(declared_classical)}\n")
            sys.stderr.flush()
            
            # ===== REFERENCED VARIABLES =====
            # Track which variables are actually used/referenced in the code
            
            referenced_quantum = set()
            referenced_classical = set()
            
            # Remove comments from content for cleaner analysis
            code_lines = []
            for line in content.split('\n'):
                # Remove inline comments
                if '//' in line:
                    line = line[:line.index('//')]
                code_lines.append(line)
            code_for_refs = '\n'.join(code_lines)
            
            # Find all identifier usage (simple approach: any word not in declaration context)
            all_identifiers = re.findall(r'\b([a-zA-Z_]\w*)\b', code_for_refs)
            
            # Determine which are quantum vs classical based on declarations
            declared_quantum_set = set(declared_quantum)
            declared_classical_set = set(declared_classical)
            declared_gates_set = set(declared_gates)
            
            # Reserved keywords to exclude
            keywords = {
                'include', 'gate', 'qubit', 'bit', 'int', 'float', 'angle', 'bool', 'complex',
                'if', 'else', 'for', 'while', 'break', 'continue', 'return',
                'def', 'let', 'const', 'var', 'box', 'cal', 'defcal', 'switch', 'case',
                'qreg', 'creg', 'true', 'false', 'pi', 'tau', 'sqrt', 'exp', 'ln', 'sin', 'cos', 'tan',
                'reset', 'measure', 'uint', 'bool', 'in', 'is', 'as'
            }
            
            # Also extract from required_vars which variables are gates vs qubits vs classical
            required_gates = set()
            required_qubits = set()
            required_classical = set()
            
            for req_var in required_vars:
                if req_var.startswith('gate '):
                    gate_name = req_var[5:].strip()
                    required_gates.add(gate_name)
                elif 'qubit' in req_var.lower():
                    # Extract name from "qubit x" or "qubit[4] x"
                    match = re.search(r'qubit(?:\[[0-9]+\])?\s+(\w+)', req_var)
                    if match:
                        required_qubits.add(match.group(1))
                else:
                    # Assume classical (bit, int, float, etc.)
                    match = re.search(r'(?:bit|int|float|angle|bool|complex)(?:\[[0-9]+\])?\s+(\w+)', req_var)
                    if match:
                        required_classical.add(match.group(1))
            
            sys.stderr.write(f"[WORKER-EXEC] Required parsed: gates={required_gates}, qubits={required_qubits}, classical={required_classical}\n")
            sys.stderr.flush()
            
            for ident in all_identifiers:
                if ident in keywords:
                    continue
                
                # Check locally declared variables first
                if ident in declared_quantum_set:
                    referenced_quantum.add(ident)
                elif ident in declared_classical_set:
                    referenced_classical.add(ident)
                elif ident in declared_gates_set:
                    # Locally declared gates being called
                    referenced_quantum.add(f"<gate {ident}>")
                # Check required variables  
                elif ident in required_qubits:
                    referenced_quantum.add(ident)
                elif ident in required_classical:
                    referenced_classical.add(ident)
                elif ident in required_gates:
                    # Required gates being called
                    referenced_quantum.add(f"<gate {ident}>")
            
            sys.stderr.write(f"[WORKER-EXEC] References: quantum={len(referenced_quantum)}, classical={len(referenced_classical)}\n")
            sys.stderr.flush()
            
            # Display parsed information
            self._emit(f"  Includes: {', '.join(includes) if includes else '(none)'}")
            
            # Show required variables if this is a continuation chunk
            if required_vars:
                self._emit(f"  Required vars from previous chunks:")
                for var in required_vars:
                    self._emit(f"    {var}")
            
            # Declared variables
            all_declared = declared_quantum + declared_classical + declared_gates
            if all_declared:
                self._emit(f"  Declared vars:")
                if declared_gates:
                    self._emit(f"    Quantum (gates): {', '.join(declared_gates)}")
                if declared_quantum:
                    self._emit(f"    Quantum (qubits): {', '.join(declared_quantum)}")
                if declared_classical:
                    self._emit(f"    Classical: {', '.join(declared_classical)}")
            else:
                if not required_vars:  # Only show "(none)" if no declared AND no required
                    self._emit(f"  Declared vars: (none)")
            
            # Referenced variables
            if referenced_quantum or referenced_classical:
                self._emit(f"  Referenced vars:")
                if referenced_quantum:
                    # Separate gate references from qubit references
                    quantum_refs = [v for v in referenced_quantum if not v.startswith('<')]
                    gate_refs = [v.replace('<gate ', '').replace('>', '') for v in referenced_quantum if v.startswith('<')]
                    
                    if quantum_refs:
                        self._emit(f"    Quantum: {', '.join(sorted(quantum_refs))}")
                    if gate_refs:
                        self._emit(f"    Gates called: {', '.join(sorted(gate_refs))}")
                if referenced_classical:
                    self._emit(f"    Classical: {', '.join(sorted(referenced_classical))}")
            else:
                if not required_vars and not all_declared:  # Only show "(none)" if empty
                    self._emit(f"  Referenced vars: (none)")
            
            # Simulate execution time
            self._emit(f"  Executing... (simulated 5s delay)")
            time.sleep(5)
            
            self._emit(f"  ✓ Simulation complete for chunk {chunk_id}")
            
        except Exception as e:
            import traceback
            self._emit(f"  ✗ Error during simulation: {e}")
            sys.stderr.write(f"[WORKER-EXEC] Exception during simulation for chunk {chunk_id}:\n")
            sys.stderr.write(traceback.format_exc())
            sys.stderr.flush()
    
    def stop(self) -> None:
        """Stop the worker server."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.server_socket.close()
            self.server_socket = None
        self._emit("Worker stopped")


def main():
    parser = argparse.ArgumentParser(
        description="Worker node for receiving quantum circuit files"
    )
    parser.add_argument("port", type=int, help="TCP port to listen on")
    parser.add_argument("--host", default="0.0.0.0", help="Host/interface to bind to (default: 0.0.0.0)")
    parser.add_argument("--output-dir", default=None, help="Directory to save received files (default: ./split-received/)")
    
    args = parser.parse_args()
    
    worker = Worker(port=args.port, host=args.host, output_dir=args.output_dir)
    worker.start()


if __name__ == "__main__":
    main()
