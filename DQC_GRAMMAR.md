# DQC Pragma Grammar

## Overview

The DQC (Distributed Quantum Computing) pragma grammar is a minimalistic ANTLR4 grammar designed to recognize pragma directives in `.dqc` files. These pragmas mark split points in quantum programs for distributed execution.

## Pragma Format

```
pragma dqc.vX.split id=N
```

Where:
- `X` is the version number (integer)
- `N` is the split-point ID (integer, starting from 1)

**Note**: Split ID 0 is reserved for the implicit initial chunk (before the first pragma).

## Grammar Files

- **DQCLexer.g4**: Lexer grammar that recognizes pragma lines and passes through all other content
- **DQCParser.g4**: Parser grammar that structures the input into lines (pragmas or other content)

## Design Principles

1. **Minimalistic**: The grammar only recognizes pragma lines; everything else is treated as pass-through content
2. **Non-invasive**: Other QASM code remains completely untouched
3. **Line-based**: Each line is either a pragma or other content
4. **Version-aware**: The version number allows for future extensions

## Usage

### Generating the Parser

```bash
./gradlew generateDQCGrammar
```

This generates Python parser code in `src/main/python/parser/generated/`:
- `DQCLexer.py`
- `DQCParser.py`
- `DQCParserVisitor.py`

### Using the Parser Wrapper

```python
from parser.dqc_parser import DQCPragmaParser

# Create parser
parser = DQCPragmaParser()

# Parse a .dqc file
pragmas = parser.parse_file('example.dqc')

# Or parse a string
content = """
OPENQASM 3.0;
qubit q;
pragma dqc.v1.split id=1
h q;
"""
pragmas = parser.parse_string(content)

# Each pragma contains:
for pragma in pragmas:
    print(f"Version: {pragma.version}")
    print(f"Split ID: {pragma.split_id}")
    print(f"Line number: {pragma.line_number}")
    print(f"Raw text: {pragma.raw_text}")
```

### Validating Pragma Sequences

```python
# Validate that split IDs are sequential and start from 1
is_valid, error = DQCPragmaParser.validate_pragma_sequence(pragmas)

if not is_valid:
    print(f"Error: {error}")
```

## Example .dqc File

```qasm
OPENQASM 3.0;
include "stdgates.inc";

// Chunk 0 (implicit - no pragma needed)
qubit[2] q;
bit[2] c;

pragma dqc.v1.split id=1
// Chunk 1 starts here
h q[0];
cx q[0], q[1];

pragma dqc.v1.split id=2
// Chunk 2 starts here
measure q -> c;
```

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
