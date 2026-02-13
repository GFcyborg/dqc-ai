# Controller Mode - Quick Start Guide

## Prerequisites

1. **DQC GUI running** - Start with: `python main.py`
2. **Worker nodes listening** - Workers should be running at the addresses in `workers.json`
3. **Circuit chunks saved** - Chunks created by clicking "Analyze & Save Chunks"

## Step-by-Step Usage

### Step 1: Prepare Your Circuit Chunks

1. **Load a circuit file** in the GUI:
   - Click `File → Open Local File...` and select a `.qasm` file
   - Or click `File → Load Example` and choose a sample circuit

2. **Mark split points**:
   - Click on lines in the source code editor where you want to split the circuit
   - Lines turn yellow to indicate split points
   - You need at least 1 split point

3. **Save chunks**:
   - Click the green `✓ Analyze & Save Chunks` button
   - Choose where to save (default: `split-out/circuit-name/`)
   - Chunks are saved as `0.qasm`, `1.qasm`, `2.qasm`, etc.

### Step 2: Launch Controller Mode

1. **Open Controller Mode**:
   - Click `Tools → Launch Controller Mode...` from the menu bar
   - A dialog window appears

2. **Select Chunks Directory**:
   - Click `Browse...` next to "Chunks Directory"
   - Navigate to your `split-out/circuit-name/` directory
   - Click "Select Folder"

3. **Select Workers Configuration**:
   - Click `Browse...` next to "Workers Configuration File"
   - Default location: `src/main/python/choreo/workers.json`
   - Or select a custom `workers.json` file
   - Click "Open"

4. **Verify Configuration**:
   - The "Workers Configuration Preview" panel shows your workers in JSON format
   - Example:
     ```json
     {
         "0": "127.0.0.1:6660",
         "1": "127.0.0.1:6661",
         "2": "127.0.0.1:6662"
     }
     ```
   - If it looks correct, proceed to next step
   - If you need different workers, select a different `workers.json` file

### Step 3: Distribute Chunks

1. **Click "Launch Distribution"**:
   - The dialog closes
   - Status bar shows: "Distributing chunks to workers..."
   - File transfer begins in the background

2. **Monitor Progress**:
   - The GUI remains responsive while distributing
   - A "Distribution Results" window appears showing status

3. **Review Results**:
   - The results window shows each file transfer:
     ```
     Found 3 .qasm files to distribute
     Using 3 workers from configuration

     Sending '0.qasm' to worker 0 (127.0.0.1:6660)...
     ✓ File '0.qasm' sent successfully
     Sending '1.qasm' to worker 1 (127.0.0.1:6661)...
     ✓ File '1.qasm' sent successfully
     Sending '2.qasm' to worker 2 (127.0.0.1:6662)...
     ✓ File '2.qasm' sent successfully
     ```

4. **Verify Success**:
   - Look for ✓ (checkmark) symbols = successful transfers
   - Look for ✗ symbols = errors
   - Error messages will explain what went wrong

## Example Workflow

```bash
# 1. Start the GUI
$ python main.py

# 2. (In GUI) File → Load Example → Select "Adder"

# 3. (In GUI) Mark split points at lines 10, 20, 30

# 4. (In GUI) Click "Analyze & Save Chunks"
#    Chunks saved to: split-out/adder/
#    ├─ 0.qasm
#    ├─ 1.qasm
#    ├─ 2.qasm
#    └─ adder.qasm

# 5. Make sure workers are running:
#    $ worker.py --port 6660 &
#    $ worker.py --port 6661 &
#    $ worker.py --port 6662 &

# 6. (In GUI) Tools → Launch Controller Mode...

# 7. (In dialog) Select directory: split-out/adder/

# 8. (In dialog) Select workers.json: src/main/python/choreo/workers.json

# 9. (In dialog) Review configuration showing:
#    {
#        "0": "127.0.0.1:6660",
#        "1": "127.0.0.1:6661",
#        "2": "127.0.0.1:6662"
#    }

# 10. (In dialog) Click "Launch Distribution"

# 11. Watch results:
#     Sending '0.qasm' to worker 0 (127.0.0.1:6660)...
#     ✓ File '0.qasm' sent successfully
#     Sending '1.qasm' to worker 1 (127.0.0.1:6661)...
#     ✓ File '1.qasm' sent successfully
#     Sending '2.qasm' to worker 2 (127.0.0.1:6662)...
#     ✓ File '2.qasm' sent successfully

# 12. Workers now have their chunks and begin execution
```

## Configuring workers.json

The `workers.json` file maps worker IDs to their network addresses:

```json
{
    "0": "127.0.0.1:6660",
    "1": "127.0.0.1:6661",
    "2": "127.0.0.1:6662"
}
```

### Format
- Key: Worker ID (as string: "0", "1", "2", ...)
- Value: Network address in format `hostname:port`

### Examples

**Local Workers**:
```json
{
    "0": "127.0.0.1:6660",
    "1": "127.0.0.1:6661",
    "2": "127.0.0.1:6662"
}
```

**Mixed Local and Remote**:
```json
{
    "0": "127.0.0.1:6660",
    "1": "127.0.0.1:6661",
    "2": "192.168.1.100:6660",
    "3": "192.168.1.101:6660"
}
```

**Remote Only**:
```json
{
    "0": "worker1.example.com:7000",
    "1": "worker2.example.com:7000",
    "2": "worker3.example.com:7000"
}
```

**Custom Configuration for Testing**:
```json
{
    "0": "localhost:5000",
    "1": "localhost:5001"
}
```

## Troubleshooting

### Problem: "Please select a chunks directory"
**Solution**: Make sure you click "Browse..." next to "Chunks Directory" and select a valid directory containing `.qasm` files

### Problem: "Please select a valid workers.json file"
**Solution**: Click "Browse..." and select a valid `workers.json` file. Check that:
- File exists
- File is named `workers.json` (or has .json extension)
- File contains valid JSON

### Problem: Workers show "✗ Connection refused"
**Solution**: 
- Check that worker nodes are running at the addresses specified in `workers.json`
- Verify the hostname/port is correct
- Make sure firewall allows connections
- Try connecting manually: `nc -zv 127.0.0.1 6660`

### Problem: Workers show "✗ Connection timeout"
**Solution**:
- Worker may be overloaded or hung
- Try restarting the worker
- Increase timeout in distributed system
- Check network connectivity

### Problem: File transferred but no mark (no ✓)
**Solution**:
- Worker may not have acknowledged the file
- Check worker logs
- Verify network connection is stable

## Tips

📝 **Naming Chunks**: Files are automatically numbered (0.qasm, 1.qasm, 2.qasm) matching worker IDs in workers.json

⚙️ **Multiple Configurations**: Create different `workers.json` files for different setups:
- `workers-local.json` - For local testing
- `workers-production.json` - For production deployment
- `workers-staging.json` - For staging environment

🔄 **Reusing Chunks**: If you split once, you can distribute multiple times to different worker configurations without re-splitting

📊 **Monitoring**: The results window shows the complete distribution log. Copy/save this output for records.

🔧 **Custom Directories**: You don't have to use `split-out/`. The dialog lets you select any directory with chunks.

## Advanced Usage

### Creating Custom Worker Configurations

```bash
# Create a custom workers.json for remote deployment
cat > my-workers.json << EOF
{
    "0": "quantum-worker-1.company.com:7000",
    "1": "quantum-worker-2.company.com:7000",
    "2": "quantum-worker-3.company.com:7000",
    "3": "quantum-worker-4.company.com:7000"
}
EOF

# Then in GUI:
# Tools → Launch Controller Mode → Select my-workers.json
```

### Batch Distribution

To distribute the same chunks to multiple worker sets:

1. Save chunks once (e.g., `split-out/circuit/0.qasm`, `1.qasm`, etc.)
2. Launch Controller Mode multiple times with different `workers.json` files
3. Each distribution uses the same chunks but sends to different workers

### Monitoring Distributed Workers

After distribution, you can check worker status:

```bash
# Check if chunk 0 arrived at worker 0
tail /path/to/worker-0/chunk-0.qasm

# Check if all chunks arrived at all workers
ls -la /path/to/worker-0/
ls -la /path/to/worker-1/
ls -la /path/to/worker-2/
```

## Menu Location

```
┌─ File
│  ├─ Open Local File...
│  ├─ Load Example
│  └─ Exit
│
┌─ Tools  ◄─── NEW MENU
│  └─ Launch Controller Mode...  ◄─── NEW OPTION
```

The new menu option is always available when the GUI starts. The menu item is disabled only if the Controller module is not available (rare).
