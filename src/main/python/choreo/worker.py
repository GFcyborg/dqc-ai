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
        Handle incoming file transfer from controller.
        
        Args:
            client_socket: Socket connection from client
            client_addr: Client address (host, port)
        """
        try:
            success, output_path = FileTransferProtocol.receive_file(client_socket, self.output_dir)
            
            if success and output_path:
                file_size = os.path.getsize(output_path)
                file_name = os.path.basename(output_path)
                self._emit(
                    f"[{client_addr[0]}:{client_addr[1]}] ✓ File '{file_name}' received successfully ({file_size} bytes)"
                )
            else:
                self._emit(f"[{client_addr[0]}:{client_addr[1]}] ✗ Failed to receive file")
        
        except Exception as e:
            self._emit(f"[{client_addr[0]}:{client_addr[1]}] Error: {e}")
        
        finally:
            client_socket.close()
    
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
