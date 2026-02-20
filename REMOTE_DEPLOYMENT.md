# Remote Worker Deployment Guide

This guide explains how to run Choreo workers on remote hosts (not just locally on the controller machine).

## Overview

The Choreo system consists of:
- **Controller**: A master node that distributes quantum circuit files
- **Workers**: Remote nodes that receive and process circuit files

Workers can run on:
- ✅ The same machine as the controller (localhost)
- ✅ Different physical hosts on a network
- ✅ Cloud instances (AWS, Azure, GCP, etc.)
- ✅ HPC cluster nodes
- ✅ Docker containers

## Quick Start (Local Development)

For testing with all nodes on your local machine:

```bash
# Terminal 1: Start Worker 0 on port 6660
python start_worker.py 6660

# Terminal 2: Start Worker 1 on port 6661
python start_worker.py 6661

# Terminal 3: Start Worker 2 on port 6662
python start_worker.py 6662

# Terminal 4: Run controller to distribute files
python start_controller.py ./split-out --config workers_filesrv.json
```

The `workers_filesrv.json` file maps worker IDs to network addresses:
```json
{
    "0": "localhost:6660",
    "1": "localhost:6661",
    "2": "localhost:6662"
}
```

## Remote Deployment

### 1. Prerequisites on Each Remote Host

Each remote host that will run a worker needs:
- Python 3.8 or higher
- No additional dependencies (choreo has no external requirements)
- Network connectivity to the controller host
- Open port for the worker service

### 2. Copy Code to Remote Host

Copy the choreo package to each remote host:

```bash
# Option A: Clone the repository
git clone <repository-url> dqc-ai
cd dqc-ai

# Option B: Copy just the choreo package
scp -r src/main/python/choreo/ user@remote-host:/opt/choreo/
scp start_worker.py user@remote-host:/opt/choreo/
```

### 3. Start Worker on Remote Host

SSH into the remote host and start the worker:

```bash
# Option 1: Using the startup script (recommended)
python3 start_worker.py 6660 --host 0.0.0.0 --output-dir /data/quantum_chunks

# Option 2: Using Python module
python3 -m choreo.worker 6660 --host 0.0.0.0 --output-dir /data/quantum_chunks

# Option 3: Direct Python script
python3 src/main/python/choreo/worker.py 6660 --host 0.0.0.0 --output-dir /data/quantum_chunks
```

**Key parameters:**
- `6660` - TCP port the worker listens on (must be unique per host)
- `--host 0.0.0.0` - Listen on all network interfaces (required for remote access)
- `--output-dir /data/quantum_chunks` - Where to save received files

### 4. Configure Controller Worker Mapping

On the controller host, create or update `workers_filesrv.json`:

```json
{
    "0": "192.168.1.100:6660",
    "1": "192.168.1.101:6661",
    "2": "10.0.0.50:6662",
    "3": "aws-instance.compute.amazonaws.com:6660"
}
```

**Important:**
- Worker IDs (keys) must be sequential starting from "0"
- Values are `hostname:port` (use IP addresses or FQDNs)
- All workers in the list must be running and accessible

### 5. Run Controller to Distribute Files

On the controller host:

```bash
python start_controller.py ./split-out --config workers_filesrv.json
```

The controller will:
1. Map each input file to a worker ID
2. Connect to each worker in sequence
3. Send the quantum circuit file to the worker
4. Send any included dependencies
5. Report success or failure

## Example: 3-Host Distributed Setup

**Setup:**
- **Host A** (Controller): `192.168.1.50`
- **Host B** (Worker 0): `192.168.1.100`
- **Host C** (Worker 1): `192.168.1.101`

**On Host B (Worker):**
```bash
ssh user@192.168.1.100
cd /path/to/dqc-ai
python3 start_worker.py 6660 --host 0.0.0.0 --output-dir ./work_output
```

**On Host C (Worker):**
```bash
ssh user@192.168.1.101
cd /path/to/dqc-ai
python3 start_worker.py 6660 --host 0.0.0.0 --output-dir ./work_output
```

**On Host A (Controller):**
```bash
# Create workers configuration
cat > workers_filesrv.json << 'EOF'
{
    "0": "192.168.1.100:6660",
    "1": "192.168.1.101:6660"
}
EOF

# Generate circuit files
# (Use GUI or generate programmatically)

# Distribute to workers
python3 start_controller.py ./split-out --config workers_filesrv.json
```

## Advanced Deployment

### Persistent Worker Service (Systemd)

Create a systemd service file `/etc/systemd/system/choreo-worker.service`:

```ini
[Unit]
Description=Choreo Quantum Worker
After=network.target

[Service]
Type=simple
User=quantum
WorkingDirectory=/opt/dqc-ai
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 /opt/dqc-ai/start_worker.py 6660 --host 0.0.0.0 --output-dir /data/quantum_chunks
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable choreo-worker
sudo systemctl start choreo-worker
sudo systemctl status choreo-worker
```

### Docker Container

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY src/main/python/choreo ./choreo
COPY start_worker.py .

EXPOSE 6660

ENTRYPOINT ["python", "start_worker.py", "6660", "--host", "0.0.0.0", "--output-dir", "/output"]
```

Build and run:
```bash
docker build -t choreo-worker .
docker run -p 6660:6660 -v worker_data:/output choreo-worker
```

### Multiple Workers per Host

To run multiple workers on a single host with different ports:

```bash
# Worker 0 on port 6660
python3 start_worker.py 6660 --output-dir ./worker0_output &

# Worker 1 on port 6661
python3 start_worker.py 6661 --output-dir ./worker1_output &

# Worker 2 on port 6662
python3 start_worker.py 6662 --output-dir ./worker2_output &
```

Update `workers_filesrv.json`:
```json
{
    "0": "thishost:6660",
    "1": "thishost:6661",
    "2": "thishost:6662"
}
```

## Troubleshooting

### Worker won't start on port
```
Error: Cannot bind to 0.0.0.0:6660
```
- Port already in use: `lsof -i :6660` to find process
- Permission denied: Use ports > 1024 or run with sudo
- Firewall blocking: Check local firewall rules

### Controller can't connect to worker
- Check worker is running: `netstat -tlnp | grep 6660`
- Check firewall: `sudo ufw allow 6660/tcp`
- Test connectivity: `nc -zv hostname 6660`
- Verify IP/hostname in config file

### Files not received
- Check worker output directory exists: `ls -la /path/to/output_dir/`
- Check disk space: `df -h /`
- Check file permissions: `ls -la` on received files
- Review controller logs for errors

### Performance Issues
- Ensure adequate network bandwidth
- Monitor CPU/memory: `top`, `htop`
- Check for network latency: `ping remote-host`
- Consider local storage performance (SSD vs HDD)

## Network Configuration

### Firewall Rules

Allow worker port on the remote host:

**UFW (Ubuntu/Debian):**
```bash
sudo ufw allow 6660/tcp
```

**firewalld (CentOS/RHEL):**
```bash
sudo firewall-cmd --permanent --add-port=6660/tcp
sudo firewall-cmd --reload
```

**iptables:**
```bash
sudo iptables -A INPUT -p tcp --dport 6660 -j ACCEPT
```

### Network Verification

Check connectivity:
```bash
# From controller, test worker accessibility
telnet remote-host 6660
nc -zv remote-host 6660
python3 -c "import socket; socket.create_connection(('remote-host', 6660), timeout=5); print('OK')"
```

## Security Considerations

⚠️ **For Development/Lab Use:**
The current implementation has no authentication or encryption. For production use, consider:

1. **VPN or SSH Tunneling:** Run workers over a VPN or SSH tunnel
   ```bash
   # SSH forward: connect via localhost:6660 which tunnels to remote:6660
   ssh -L 6660:localhost:6660 user@remote-host
   ```

2. **Network Isolation:** Place workers on a private network
3. **Firewall Rules:** Restrict controller IP in firewall rules
4. **Authentication:** Add authentication layer (future enhancement)
5. **Encryption:** Add TLS/SSL (future enhancement)

## Python API Usage

You can also start workers programmatically:

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'main' / 'python'))

from choreo import Worker

# Start worker on port 6660
worker = Worker(
    port=6660,
    host="0.0.0.0",
    output_dir="./quantum_chunks"
)
worker.start()
```

## Performance Tips

1. **Local Storage:** Use fast local disk for output directory
2. **Network:** Dedicated network for worker-controller communication
3. **Scaling:** More workers = better parallelization
4. **Monitoring:** Log output to file for debugging
   ```bash
   python3 start_worker.py 6660 > worker.log 2>&1 &
   ```
5. **Resource Allocation:** Adequate CPU/RAM for simulation

## Summary

Choreo workers are designed to be easily deployable on remote hosts with minimal setup:

✅ No external dependencies  
✅ Simple network protocol  
✅ Configurable ports and interfaces  
✅ Works on standard Python 3.8+  
✅ Suitable for cloud, HPC, and on-premises deployment  

For any issues or questions, check the main [Choreo README](README.md).
