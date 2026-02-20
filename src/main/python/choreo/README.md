# Choreo: Controller-Worker Orchestration System

Distributed orchestration system for quantum circuit processing. Implements a controller-worker architecture for distributing quantum circuit files across multiple nodes.

Workers can run on **local machine** (for GUI integration) or **remote hosts** (standalone deployment for production).

## Architecture

- **Controller**: Coordinates task distribution to worker nodes based on a configuration mapping
- **Worker**: Listens for incoming files and processes them independently  
- **Protocol**: Binary file transfer protocol for reliable node-to-node communication

⚠️ **For remote worker deployment, see [REMOTE_DEPLOYMENT.md](../../REMOTE_DEPLOYMENT.md)**

## Quick Start

### 1. Prepare Workers Configuration

Copy and edit `workers_filesrv.json.example` to `workers_filesrv.json`:

```json
{
    "0": "127.0.0.1:6660",
    "1": "127.0.0.1:6661",
    "2": "127.0.0.1:6662"
}
```

Maps worker ID → `host:port`

### 2. Start Worker Nodes

```bash
# Terminal 1: Worker 0
python -m choreo.worker 6660

# Terminal 2: Worker 1 (on different host)
python -m choreo.worker 6661 --host 10.22.2.69 --output-dir ./work_output

# Terminal 3: Worker 2
python -m choreo.worker 6662 --host 10.22.2.69 --output-dir ./work_output
```

### 3. Run Controller

Distribute files from an input directory:

```bash
python -m choreo.controller ./input_files/ --config workers_filesrv.json
```

Files are matched to workers in order:
- `0.qasm` → Worker 0
- `1.qasm` → Worker 1
- `2.qasm` → Worker 2
- etc.

## Python API

### Using the Controller programmatically

```python
from choreo import Controller
from pathlib import Path

config_file = Path("workers_filesrv.json")
controller = Controller(config_file)
controller.distribute_files("./input_files/")
```

### Using a Worker programmatically

```python
from choreo import Worker

worker = Worker(port=6660, output_dir="./work_output")
worker.start()
```

## File Transfer Protocol

Simple binary protocol for reliable file transmission:

```
[file_name_length: 4 bytes (big-endian)]
[file_name: UTF-8 string]
[content_length: 4 bytes (big-endian)]
[content: binary data]
```

Upon successful receipt, worker responds with: `ACK` (3 bytes)

## Configuration

### workers_filesrv.json

Maps worker IDs (0, 1, 2...) to their network addresses:

```json
{
    "0": "host1:6660",
    "1": "host2:6661",
    "2": "host3:6662"
}
```

- Keys must be sequential starting from "0"
- Values are `hostname:port` pairs
- Supports both localhost and remote hosts
- Missing worker IDs are skipped with a warning

## Features

- **Standalone**: Works independently, minimal integration required
- **CLI-capable**: Full command-line interface for each component
- **Configurable**: Flexible worker mapping and output directories
- **Robust**: Error handling and connection management
- **Threaded**: Workers handle multiple concurrent connections
- **Simple protocol**: Binary format for efficient file transfer

## Error Handling

- Connection timeouts if worker not responding → continues to next worker
- Connection refused → reports worker not running on specified port
- Missing configuration file → exits with clear error message
- Invalid worker addresses → skipped with warning
- Missing files → controller exits with error

## Default Directories

- **Worker output**: `./work_received/` (customizable via `--output-dir`)
- **Config lookup**: `choreo/workers_filesrv.json` (customizable via `--config`)
