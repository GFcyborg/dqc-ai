# DQC - OpenQASM Splitter

Split quantum circuits into distributed chunks with automatic variable dependency analysis.

## Quick Start

**Requirements**: Python 3.8+, Java 8+

```bash
./gradlew build      # Setup everything
./gradlew run        # Start GUI
```

## Basic Usage

1. **Load a circuit** → `File → Open Local File` or `File → Load Example`
2. **Mark split points** → Click lines where you want to split
3. **View variables** → See dependencies in "Variable Analysis" tab
4. **Save chunks** → Click `✓ Analyze & Save Chunks`
5. **Optional: Distribute** → `Tools → Controller` to send chunks to workers

## Features

- ✅ Click-based split point marking
- ✅ **Automatic variable dependency tracking** (see "How Variable Analysis Works" below)
- ✅ AST visualization
- ✅ OpenQASM 3.0 type support
- ✅ Include file support
- ✅ Distribute chunks to worker nodes
- ✅ Cross-platform

## How Variable Analysis Works

The application identifies which variables are needed for each chunk through a multi-pass analysis:

### 1. **Variable Declaration Tracking**
The parser scans the entire circuit to find all variable declarations:
- `qubit[n]` - quantum registers
- `bit[n]` - classical bit registers
- `int`, `float`, `bool`, `angle`, `complex`, `duration` - scalar types

For each variable, it records: name, type, size, and declaration line.

### 2. **Usage Analysis Per Chunk**
For each code chunk (section between split points):
- Identifies all variable references (read/write operations)
- Tracks which lines use which variables
- Determines what needs to be available before the chunk executes

### 3. **Dependency Resolution**
The chunks are analyzed in order to track:
- **Initial dependencies** - Variables declared before chunk 0 that chunk 0 needs
- **Inter-chunk dependencies** - Variables that one chunk produces that the next chunk needs
- **Transitive dependencies** - Variables indirectly required through operations

### Example

```qasm
qubit[3] q;        // Line 1: Variable declaration
bit[3] c;          // Line 2: Variable declaration

// Chunk 0 (before first split point)
h q[0];            // Uses q
cx q[0], q[1];     // Uses q

pragma dqc.v1.split id=1

// Chunk 1
c = measure q;     // Uses q, produces c
```

Analysis output:
- **Chunk 0**: Declares `q, c` | Uses `q` | Produces `q, c` (state changes)
- **Chunk 1**: Needs `q` (state from chunk 0) | Uses `q, c` | Produces `c` (measurement result)

When distributing:
- Chunk 0 receives initial declarations for `q, c`
- Chunk 1 receives the `q` state from chunk 0 plus the `c` variable

## Commands

```bash
./gradlew build                # Build and setup everything
./gradlew run                  # Run the GUI
./gradlew test                 # Run all tests
./gradlew clean                # Clean build artifacts
./gradlew generateGrammarSource # Generate parsers only
./gradlew setupPythonEnv       # Setup Python environment only
```

## Testing

```bash
./gradlew test
# or
python3 tests/run_all_tests.py
```

## Troubleshooting

| Error | Solution |
|-------|----------|
| "Parser not available" | Run `./gradlew build` |
| "ModuleNotFoundError: antlr4" | Run `./gradlew build` |
| Grammar download fails | Check internet, retry, or use files in `src/main/antlr4/` |
| GUI doesn't start | Install Tkinter: `sudo apt-get install python3-tk` (Linux) |

## File Structure

```
dqc-ai/
├── main.py                           # Entry point
├── src/main/python/
│   ├── parser/                       # OpenQASM parsing
│   │   └── generated/                # ANTLR-generated parsers
│   ├── analyzer/                     # Variable dependency analysis
│   └── gui/                          # Tkinter GUI
├── src/main/antlr4/                  # Grammar files
├── tests/                            # Test suites
└── split-out/                        # Output directory
```
