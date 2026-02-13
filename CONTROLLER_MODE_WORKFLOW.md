# Controller Mode - Visual Workflow Guide

## User Interface Flow

```
┌─────────────────────────────────────────────────────────────┐
│              DQC - OpenQASM Splitter GUI                    │
├─────────────────────────────────────────────────────────────┤
│ File  Tools                                                  │
│       └─ Launch Controller Mode...  ◄─── NEW MENU ITEM      │
└─────────────────────────────────────────────────────────────┘
         ↓ Click
┌─────────────────────────────────────────────────────────────┐
│     Controller Mode - Distribute Chunks to Workers          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Chunks Directory                                           │
│  ┌────────────────────────────────────────────────┬────────┐
│  │ /path/to/split-out/circuit-name/  │ Browse...  │       │
│  └────────────────────────────────────────────────┴────────┘
│                                                              │
│  Workers Configuration File                                │
│  ┌────────────────────────────────────────────────┬────────┐
│  │ /path/to/workers.json  │ Browse...             │       │
│  └────────────────────────────────────────────────┴────────┘
│                                                              │
│  Workers Configuration Preview                             │
│  ┌────────────────────────────────────────────────────────┐
│  │ {                                                      │
│  │     "0": "127.0.0.1:6660",                           │
│  │     "1": "127.0.0.1:6661",                           │
│  │     "2": "127.0.0.1:6662"                            │
│  │ }                                                      │
│  └────────────────────────────────────────────────────────┘
│                                                              │
│                 ┌──────────────────────┐                    │
│                 │ Launch Distribution  │ ◄─ Click           │
│                 │        Cancel        │                    │
│                 └──────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
         ↓ Distribution runs in background
┌─────────────────────────────────────────────────────────────┐
│             Distribution Results                            │
├─────────────────────────────────────────────────────────────┤
│ Found 3 .qasm files to distribute                           │
│ Using 3 workers from configuration                          │
│                                                              │
│ Sending '0.qasm' to worker 0 (127.0.0.1:6660)...           │
│ ✓ File '0.qasm' sent successfully                          │
│ Sending '1.qasm' to worker 1 (127.0.0.1:6661)...           │
│ ✓ File '1.qasm' sent successfully                          │
│ Sending '2.qasm' to worker 2 (127.0.0.1:6662)...           │
│ ✓ File '2.qasm' sent successfully                          │
│                                                              │
│                    ┌────────┐                               │
│                    │  Close │                               │
│                    └────────┘                               │
└─────────────────────────────────────────────────────────────┘
         ↓ Users reviewed results
    Distribution Complete
```

## Complete Workflow: From Circuit to Distributed Execution

```
START
  ↓
┌─────────────────────────────────────────┐
│ 1. Load Circuit File                    │
│    File → Open Local File...            │
│    or File → Load Example                │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 2. Mark Split Points                    │
│    Click on lines in source code        │
│    to mark where chunks should split    │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 3. Save Chunks                          │
│    Click "Analyze & Save Chunks"        │
│    Creates: split-out/circuit-name/     │
│            ├─ 0.qasm                    │
│            ├─ 1.qasm                    │
│            ├─ 2.qasm                    │
│            └─ [original files]          │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 4. Launch Controller Mode ◄─ NEW        │
│    Tools → Launch Controller Mode...    │
│    Select chunks directory              │
│    Select/verify workers.json           │
│    Click "Launch Distribution"          │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 5. Distribute to Workers                │
│    Controller sends:                    │
│    0.qasm → Worker 0 (127.0.0.1:6660)   │
│    1.qasm → Worker 1 (127.0.0.1:6661)   │
│    2.qasm → Worker 2 (127.0.0.1:6662)   │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 6. View Distribution Results            │
│    Results window shows success/error   │
│    for each file transfer               │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ 7. Workers Execute                      │
│    Each worker processes their chunk    │
│    Parallel execution                   │
└─────────────────────────────────────────┘
  ↓
END
```

## File Distribution Pattern

```
Controller Node                          Worker Nodes
┌─────────────────────┐                 ┌─────────────────┐
│                     │                 │   Worker 0      │
│ split-out/          │ ─ 0.qasm ────→  │ (localhost:6660)│
│ circuit-name/       │                 │                 │
│ ├─ 0.qasm          │                 │ Receives:       │
│ ├─ 1.qasm          │ ─ 1.qasm ────→  │ 0.qasm          │
│ ├─ 2.qasm          │                 └─────────────────┘
│ └─ ...             │                 ┌─────────────────┐
│                     │                 │   Worker 1      │
│ workers.json       │                 │ (localhost:6661)│
│ │                 │                 │                 │
│ ├─ "0":           │                 │ Receives:       │
│ │   "127.0.0.1:   │ ─ 2.qasm ────→  │ 1.qasm          │
│ │    6660",       │                 └─────────────────┘
│ ├─ "1":           │                 ┌─────────────────┐
│ │   "127.0.0.1:   │                 │   Worker 2      │
│ │    6661",       │                 │ (localhost:6662)│
│ └─ "2":           │                 │                 │
│     "127.0.0.1:   │ ────────────────→│ Receives:       │
│      6662"        │                 │ 2.qasm          │
│                     │                 └─────────────────┘
└─────────────────────┘
```

## Configuration Example

### workers.json Format
```json
{
    "0": "127.0.0.1:6660",
    "1": "127.0.0.1:6661",
    "2": "127.0.0.1:6662",
    "3": "192.168.1.100:6660",
    "4": "remote-worker.example.com:7000"
}
```

Maps worker IDs to their network addresses:
- ID "0" → localhost at port 6660
- ID "1" → localhost at port 6661
- ID "2" → localhost at port 6662
- ID "3" → Different machine on local network
- ID "4" → Remote worker across network

## Error Handling

```
Possible Errors & Responses:

Missing Chunks Directory
  ↓
  ❌ "Please select a chunks directory"
  ↑
  User selects directory

Invalid workers.json
  ↓
  ❌ "Please select a valid workers.json file"
  ↑
  User selects valid file

Worker not listening
  ↓
  Connection window shows:
  "✗ Connection refused (worker not listening on 127.0.0.1:6660)"
  ↑
  User checks worker status

Network timeout
  ↓
  Connection window shows:
  "✗ Connection timeout (worker may not be running)"
  ↑
  User waits and retries
```

## Key Implementation Details

### Threading Architecture
```
Main GUI Thread                Background Distribution Thread
       │                                    │
       │ Click "Launch Distribution"        │
       ├───────────────────────────────────→│
       │                        │ Run Controller.distribute_files()
       │                        │ Capture output
       │                        │ Send files to workers
       │                        │
       │ ← EOF (thread.after)  │
       │ Show results window    │
       │                        │
     GUI responsive           Thread completes
     during distribution       (daemon=True)
```

### Status Updates Flow
```
1. User clicks "Launch Distribution"
2. Dialog closes, dialog is destroyed
3. Status bar shows: "Distributing chunks to workers..."
4. Background thread starts
5. Files are sent to workers
6. Background thread completes
7. root.after(0, ...) queues result display
8. Results window appears
9. Status bar shows: "Distribution completed!"
```
