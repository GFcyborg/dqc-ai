# GUI Features

## Feature 1: Perfect Font Alignment

Line numbers are perfectly aligned with code lines - no misalignment issues.

## Feature 2: Dynamic Example Loading

Access 20+ official OpenQASM examples directly from GitHub:

**File → Load Example**
- Adder, Alignment, Arrays, Cphase, DD, Defcal, Gateteleport
- Inverseqft1, Inverseqft2, Ipe, MSD, QEC, QFT, QPT
- RB, RUS, SCQEC, T1, Teleport, Varteleport, VQE
- (Fetched from official OpenQASM repository)

Automatically updates when new examples are added.

## Feature 3: Controller Mode - Distribute Chunks to Workers

Distribute saved circuit chunks to worker nodes for parallel execution.

### How to Use

1. **Save chunks** → Click `✓ Analyze & Save Chunks` (creates `split-out/<circuit-name>/`)
2. **Launch controller** → `Tools → Controller Mode...`
3. **Select directory** → Choose the `split-out/<circuit-name>/` folder
4. **Select config** → Choose `workers_filesrv.json` file (default: `src/main/python/choreo/workers_filesrv.json`)
5. **Review config** → Preview shows worker addresses
6. **Distribute** → Click "Launch Distribution"
7. **Monitor** → Results window shows each file being sent

### workers_filesrv.json Format

```json
{
    "0": "127.0.0.1:6660",
    "1": "127.0.0.1:6661",
    "2": "127.0.0.1:6662"
}
```

Maps worker IDs to network addresses (hostname:port).

### Features

- ✅ Easy file/folder browser for selecting chunks and config
- ✅ Configuration preview before distribution
- ✅ Non-blocking background distribution
- ✅ Live results window showing transfer status
- ✅ Graceful error handling for missing workers or network issues

### Example

```bash
# In GUI:
1. File → Load Example → Teleport
2. Mark split points at lines 8, 13
3. Analyze & Save Chunks
   # Saves to: split-out/teleport/0.qasm, 1.qasm, 2.qasm

4. Tools → Controller Mode
5. Select Directory: split-out/teleport/
6. Select Config: src/main/python/choreo/workers_filesrv.json
7. Launch Distribution
# Sends 0.qasm to worker 0, 1.qasm to worker 1, 2.qasm to worker 2
```

## Testing

```bash
./gradlew test
# or
python3 tests/test_gui_enhancements.py
```

