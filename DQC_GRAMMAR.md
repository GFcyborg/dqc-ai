# DQC Pragma Grammar

Marks split points in quantum circuits for distributed execution.

## Format

```
pragma dqc.vX.split id=N
```

- **X** = version number (integer, e.g., 1)
- **N** = split ID (integer, starting from 1)

Example:
```qasm
OPENQASM 3.0;
qubit[2] q;

h q[0];
cx q[0], q[1];

pragma dqc.v1.split id=1

measure q;
```

## Usage

### In Code

Simply insert pragmas where you want to mark split points:

```qasm
// Chunk 0 - preparation
qubit[3] q;
h q;

pragma dqc.v1.split id=1

// Chunk 1 - operations
cx q[0], q[1];

pragma dqc.v1.split id=2

// Chunk 2 - measurement
measure q;
```

### From GUI

Click lines in the "Source Code" tab - the GUI automatically marks split points and exports chunks with appropriate pragmas.

## Grammar Files

- `dqcLexer.g4` - Recognizes pragma lines
- `dqcParser.g4` - Structures lines into pragmas or other content

Generated parsers in: `src/main/python/parser/generated/`

## Python API

```python
from parser.dqc_parser import DQCPragmaParser

parser = DQCPragmaParser()
pragmas = parser.parse_file('circuit.dqc')

for pragma in pragmas:
    print(f"ID: {pragma.split_id}, Line: {pragma.line_number}")
```

Each pragma contains:
- `version` - Version number from pragma
- `split_id` - Split identifier
- `line_number` - Line where pragma appears
- `raw_text` - Original line text


This file defines 3 chunks:
- **Chunk 0** (lines 1-6): Declarations and setup
- **Chunk 1** (lines 8-10): Bell state preparation
- **Chunk 2** (lines 12-13): Measurement

## Validation Rules

1. Split IDs must start from 1 (0 is reserved for the implicit first chunk)
2. Split IDs must be sequential (no gaps)
3. Each pragma must be on its own line
4. The pragma format must be exact (whitespace between tokens is flexible)

## Future Extensions

The versioning system (`vX`) allows for future extensions without breaking existing files:
- Different split types (e.g., `pragma dqc.v2.split type=entanglement id=N`)
- Metadata annotations (e.g., `pragma dqc.v2.metadata key=value`)
- Constraints (e.g., `pragma dqc.v2.constraint max_qubits=10`)

For now, the parser simply recognizes and extracts the pragmas without performing any actions on them.
