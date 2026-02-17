# Controller Mode - Release Notes

## What's New

Added **Controller Mode** to distribute saved quantum circuit chunks to worker nodes.

### New Features

✅ **Distribute Chunks** - `Tools → Controller Mode...`
✅ **Worker Configuration** - Support for custom `workers.json` files
✅ **Configuration Preview** - See workers before distributing
✅ **Background Distribution** - Non-blocking file transfers
✅ **Results Window** - Live status updates for each file

## How to Use

1. **Save chunks** → `✓ Analyze & Save Chunks` (creates `split-out/<circuit-name>/`)
2. **Configure workers** → Edit `src/main/python/choreo/workers.json`
3. **Distribute** → `Tools → Controller Mode...`
4. **Select directory** → Choose `split-out/<circuit-name>/`
5. **Launch** → Files sent to workers in background

## Example

```bash
# In GUI:
File → Load Example → Teleport
Click lines 8, 13 (mark splits)
Analyze & Save Chunks
# Creates: split-out/teleport/0.qasm, 1.qasm, 2.qasm

Tools → Controller Mode
Select: split-out/teleport/
Verify: workers.json shows 3 workers
Launch Distribution

# Output:
# ✓ 0.qasm sent to worker 0
# ✓ 1.qasm sent to worker 1
# ✓ 2.qasm sent to worker 2
```

## Files Modified

- **src/main/python/gui/main_window.py** - Added 4 new methods for controller mode
- **src/main/python/choreo/controller.py** - Modified `distribute_files()` to raise exceptions instead of exit

## Documentation

- [CONTROLLER_MODE_QUICKSTART.md](CONTROLLER_MODE_QUICKSTART.md) - Quick start guide
- [CONTROLLER_MODE_WORKFLOW.md](CONTROLLER_MODE_WORKFLOW.md) - Workflow examples
- [CONTROLLER_MODE_IMPLEMENTATION.md](CONTROLLER_MODE_IMPLEMENTATION.md) - Technical details

