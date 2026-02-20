"""
Binary file transfer and execution protocol for controller-worker communication.

File transfer protocol format:
  [command:1 byte = 0x01]
  [file_name_length:4 bytes (big-endian)]
  [file_name:UTF-8]
  [content_length:4 bytes (big-endian)]
  [content:binary data]

Execution protocol format:
  [command:1 byte = 0x02]
  [chunk_id_length:4 bytes (big-endian)]
  [chunk_id:UTF-8]

Responses:
  b'ACK' - File received successfully
  b'ACK_STARTED' - Execution started
  b'DONE' - Execution completed
"""

import socket
from typing import Tuple, Optional


class FileTransferProtocol:
    """Handles binary file transfer and execution commands between nodes."""
    
    DEFAULT_CHUNK_SIZE = 4096
    TIMEOUT = 10
    
    # Commands
    CMD_FILE_TRANSFER = b'\x01'
    CMD_EXECUTE_CHUNK = b'\x02'
    
    # Responses
    ACK = b'ACK'
    ACK_STARTED = b'ACK_STARTED'
    DONE = b'DONE'
    
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
            
            # Send command byte + file transfer data
            sock.sendall(FileTransferProtocol.CMD_FILE_TRANSFER + name_len + file_name_bytes + content_len + file_content)
            
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
            # Command byte already read by caller
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

    @staticmethod
    def send_execute_command(sock: socket.socket, chunk_id: str) -> Tuple[bool, bool]:
        """
        Send an execution command to a worker.
        
        Args:
            sock: Connected socket
            chunk_id: ID of the chunk to execute
            
        Returns:
            Tuple of (started: bool, completed: bool)
        """
        try:
            chunk_id_bytes = chunk_id.encode('utf-8')
            id_len = len(chunk_id_bytes).to_bytes(4, byteorder='big')
            
            # Send command byte + chunk ID
            message = FileTransferProtocol.CMD_EXECUTE_CHUNK + id_len + chunk_id_bytes
            sock.sendall(message)
            
            # Wait for ACK_STARTED
            ack = sock.recv(len(FileTransferProtocol.ACK_STARTED))
            if ack != FileTransferProtocol.ACK_STARTED:
                return False, False
            
            # Wait for DONE
            done = sock.recv(len(FileTransferProtocol.DONE))
            return True, done == FileTransferProtocol.DONE
            
        except socket.timeout as e:
            return False, False
        except Exception as e:
            return False, False

    @staticmethod
    def receive_execute_command(sock: socket.socket) -> Optional[str]:
        """
        Receive an execution command from controller.
        
        Args:
            sock: Connected socket
            
        Returns:
            chunk_id if successful, None otherwise
        """
        try:
            # Command byte already read by caller
            id_len_bytes = sock.recv(4)
            if not id_len_bytes:
                return None
            
            id_len = int.from_bytes(id_len_bytes, byteorder='big')
            chunk_id = sock.recv(id_len).decode('utf-8')
            
            return chunk_id
            
        except Exception as e:
            print(f"Error receiving execute command: {e}")
            return None
