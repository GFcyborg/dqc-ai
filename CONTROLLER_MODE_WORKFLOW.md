# Controller Mode Workflow

## Complete Process

```
1. Load Circuit
   └─> File → Open Local File or Load Example

2. Mark Split Points
   └─> Click lines in Source Code tab

3. Save Chunks
   └─> Analyze & Save Chunks → split-out/<name>/0.qasm, 1.qasm, 2.qasm

4. Configure Workers (if needed)
   └─> Edit src/main/python/choreo/workers.json

5. Distribute
   └─> Tools → Launch Controller Mode
       ├─ Select chunks directory
       ├─ Verify worker config
       └─ Launch Distribution

6. Workers Receive Files
   └─> Each worker gets its assigned chunk file
```

## Example: Quantum Teleportation

```qasm
OPENQASM 3.0;
include "stdgates.inc";

qubit[3] q;
bit[3] c;

// Chunk 0: Bell pair
h q[0];
cx q[0], q[1];
// ^^ Split here ^^

// Chunk 1: Measurements
cx q[0], q[2];
h q[0];
measure q -> c;
// ^^ Split here ^^

// Chunk 2: Corrections
if (c[1]) x q[1];
if (c[0]) z q[1];
```

### GUI Steps

1. **Load**: File → Load Example → Teleport
2. **Mark**: Click lines 9 and 14
3. **Save**: Analyze & Save Chunks
   - Creates: `split-out/teleport/0.qasm`, `1.qasm`, `2.qasm`
4. **Distribute**: Tools → Launch Controller Mode
   - Select: `split-out/teleport/`
   - Verify: workers.json shows 3 workers
   - Launch: Sends files to workers

### Output

```
Distributing chunks to workers...

Sending '0.qasm' to worker 0 (127.0.0.1:6660)... ✓
Sending '1.qasm' to worker 1 (127.0.0.1:6661)... ✓
Sending '2.qasm' to worker 2 (127.0.0.1:6662)... ✓

All files distributed successfully!
```

## Configuration

### workers.json Format

```json
{
    "0": "127.0.0.1:6660",
    "1": "127.0.0.1:6661",
    "2": "127.0.0.1:6662"
}
```

- Key: Worker ID (0, 1, 2, ...)
- Value: hostname:port address
- Files mapped in order: 0.qasm → worker 0, 1.qasm → worker 1, etc.

### Custom Configuration

Create a custom `workers.json`:
```json
{
    "0": "worker1.example.com:6660",
    "1": "worker2.example.com:6660",
    "2": "worker3.example.com:6660"
}
```

Then select it in the Controller Mode dialog.

