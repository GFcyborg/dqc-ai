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
        Simulate execution of a QASM chunk.
        
        Args:
            chunk_id: ID of the chunk to execute (e.g., "0", "1", "2")
        """
        import re
        import time
        
        # Find the chunk file
        chunk_file = os.path.join(self.output_dir, f"{chunk_id}.qasm")
        
        if not os.path.exists(chunk_file):
            self._emit(f"  ✗ Error: Chunk file '{chunk_id}.qasm' not found in {self.output_dir}")
            return
        
        self._emit(f"  Simulating execution of chunk '{chunk_id}.qasm'...")
        
        # Parse the file
        includes = []
        variables = []
        
        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract include statements
            include_pattern = re.compile(r'^\s*include\s+"([^"]+)"\s*;', re.MULTILINE)
            includes = include_pattern.findall(content)
            
            # Extract variable declarations (qubit, bit, int, float, etc.)
            var_pattern = re.compile(r'^\s*(?:qubit|bit|int|float|angle|bool)\s+(\w+)', re.MULTILINE)
            variables = var_pattern.findall(content)
            
            # Display parsed information
            if includes:
                self._emit(f"  Includes: {', '.join(includes)}")
            else:
                self._emit(f"  Includes: (none)")
            
            if variables:
                self._emit(f"  Variables: {', '.join(variables)}")
            else:
                self._emit(f"  Variables: (none)")
            
            # Simulate execution time
            self._emit(f"  Executing... (simulated 5s delay)")
            time.sleep(5)
            
            self._emit(f"  ✓ Simulation complete for chunk {chunk_id}")
            
        except Exception as e:
            self._emit(f"  ✗ Error during simulation: {e}")
    
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
