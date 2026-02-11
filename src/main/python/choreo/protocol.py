"""
Binary file transfer protocol for controller-worker communication.

Protocol format:
  [file_name_length:4 bytes (big-endian)]
  [file_name:UTF-8]
  [content_length:4 bytes (big-endian)]
  [content:binary data]

Upon successful receipt, recipient sends: b'ACK' (3 bytes)
"""

import socket
from typing import Tuple, Optional


class FileTransferProtocol:
    """Handles binary file transfer between nodes."""
    
    DEFAULT_CHUNK_SIZE = 4096
    TIMEOUT = 10
    ACK = b'ACK'
    
    @staticmethod
    def send_file(sock: socket.socket, file_path: str, file_name: str) -> bool:
        """
        Send a file over socket with metadata headers.
        
        Args:
            sock: Connected socket
            file_path: Full path to file to send
            file_name: Name of file as seen by recipient
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            file_name_bytes = file_name.encode('utf-8')
            name_len = len(file_name_bytes).to_bytes(4, byteorder='big')
            content_len = len(file_content).to_bytes(4, byteorder='big')
            
            sock.sendall(name_len + file_name_bytes + content_len + file_content)
            
            ack = sock.recv(3)
            return ack == FileTransferProtocol.ACK
            
        except Exception as e:
            print(f"Error sending file: {e}")
            return False
    
    @staticmethod
    def receive_file(sock: socket.socket, output_dir: str) -> Tuple[bool, Optional[str]]:
        """
        Receive a file over socket with metadata headers.
        
        Args:
            sock: Connected socket
            output_dir: Directory to save received file
            
        Returns:
            Tuple of (success: bool, file_path: Optional[str])
        """
        try:
            name_len_bytes = sock.recv(4)
            if not name_len_bytes:
                return False, None
            
            name_len = int.from_bytes(name_len_bytes, byteorder='big')
            file_name = sock.recv(name_len).decode('utf-8')
            
            content_len_bytes = sock.recv(4)
            content_len = int.from_bytes(content_len_bytes, byteorder='big')
            
            file_content = b''
            remaining = content_len
            while remaining > 0:
                chunk = sock.recv(min(FileTransferProtocol.DEFAULT_CHUNK_SIZE, remaining))
                if not chunk:
                    break
                file_content += chunk
                remaining -= len(chunk)
            
            import os
            output_path = os.path.join(output_dir, file_name)
            with open(output_path, 'wb') as f:
                f.write(file_content)
            
            sock.sendall(FileTransferProtocol.ACK)
            return True, output_path
            
        except Exception as e:
            print(f"Error receiving file: {e}")
            return False, None
