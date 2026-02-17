# Quick Start

## Setup (1 minute)

```bash
./gradlew build  # Downloads grammar, generates parsers, installs dependencies
./gradlew run    # Opens GUI
```

## Basic Workflow (2 minutes)

1. **Load Circuit**: `File → Load Example → QFT` (or `Open Local File`)
2. **Mark Splits**: Click lines to mark split points (they highlight in yellow)
3. **Review**: Switch to `Variable Analysis` tab to see dependencies
4. **Save**: Click `✓ Analyze & Save Chunks`

Chunks are saved to `split-out/<filename>/` with dependency comments.

## Example: Quantum Teleportation

```bash
# In GUI:
File → Load Example → Teleport

# Mark splits at:
# Line 8 (after Bell pair)
# Line 13 (after measurements)

# In Variable Analysis tab, see:
# Chunk 0: Bell pair operations
# Chunk 1: Measurements  
# Chunk 2: Corrections

Analyze & Save Chunks
```

## Common Tasks

| Task | Steps |
|------|-------|
| Use your own QASM file | `File → Open Local File → Select file` |
| See circuit structure | Switch to `AST View` tab |
| Distribute to workers | `Tools → Launch Controller Mode` |
| Run tests | `./gradlew test` or `python3 tests/run_all_tests.py` |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Parser not available" | `./gradlew build` |
| Tkinter missing (Linux) | `sudo apt-get install python3-tk` |
| Can't download examples | Check internet, try local file instead |

## Next

- [README.md](README.md) - Full documentation
- [DQC_GRAMMAR.md](DQC_GRAMMAR.md) - Pragma format
- [CONTROLLER_MODE_QUICKSTART.md](CONTROLLER_MODE_QUICKSTART.md) - Distributed execution

