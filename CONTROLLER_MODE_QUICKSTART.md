# Controller Mode Quick Start

Distribute saved quantum circuit chunks to worker nodes.

## Setup

1. **Save chunks** from GUI: `✓ Analyze & Save Chunks` (creates `split-out/<circuit-name>/`)
2. **Configure workers**: Edit `src/main/python/choreo/workers.json`

Example workers.json:
```json
{
    "0": "127.0.0.1:6660",
    "1": "127.0.0.1:6661",
    "2": "127.0.0.1:6662"
}
```

## Distribute

1. **Launch Controller Mode**: `Tools → Launch Controller Mode...`
2. **Select chunks directory**: `split-out/<circuit-name>/`
3. **Verify config**: See workers in "Workers Configuration Preview"
4. **Launch Distribution**: Click "Launch Distribution"
5. **Monitor**: Results window shows each file transfer status

## Example

```bash
# In GUI:
1. File → Load Example → Teleport
2. Click lines 8 and 13 to mark split points
3. Analyze & Save Chunks
   # Creates: split-out/teleport/0.qasm, 1.qasm, 2.qasm

4. Tools → Launch Controller Mode
5. Directory: split-out/teleport/
6. Config: src/main/python/choreo/workers.json
7. Launch Distribution

# Output:
# File '0.qasm' sent to worker 0 (127.0.0.1:6660)... ✓
# File '1.qasm' sent to worker 1 (127.0.0.1:6661)... ✓
# File '2.qasm' sent to worker 2 (127.0.0.1:6662)... ✓
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Controller Mode" menu disabled | Make sure `choreo/controller.py` module exists |
| Can't select chunks directory | Run `Analyze & Save Chunks` first |
| Worker not found error | Check workers.json addresses and that workers are listening |
| Network timeout | Verify worker nodes are reachable (ping/netstat) |

