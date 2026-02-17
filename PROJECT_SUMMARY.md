# Project Summary

A tool for splitting quantum circuits (OpenQASM 3.0) into distributed chunks with automatic variable dependency analysis.

## What It Does

1. **Parses quantum circuits** using OpenQASM 3.0 grammar (ANTLR4)
2. **Tracks variables** across code sections
3. **Identifies dependencies** - which variables each chunk needs
4. **Exports chunks** as separate `.qasm` files with dependency annotations
5. **Optional: Distributes** chunks to worker nodes for parallel execution

## Components

### Parser Module (`src/main/python/parser/`)
- OpenQASM 3.0 parsing
- DQC pragma recognition (`pragma dqc.vX.split id=N`)
- Uses ANTLR4-generated code

### Analyzer Module (`src/main/python/analyzer/`)
- Variable declaration tracking
- Usage analysis per chunk
- Dependency resolution
- Supports all OpenQASM types (qubit, bit, int, float, angle, bool, complex, duration, stretch)

### GUI Module (`src/main/python/gui/`)
- Click-based split point marking
- Tkinter-based interface
- 20+ example circuits from GitHub
- AST visualization
- Include file support

## Project Structure

```
dqc-ai/
├── main.py                     # Entry point
├── src/main/
│   ├── python/
│   │   ├── parser/            # OpenQASM parsing (ANTLR4)
│   │   ├── analyzer/          # Variable dependency analysis
│   │   └── gui/               # Tkinter GUI
│   └── antlr4/                # Grammar files
├── tests/                     # Test suites (10+ tests)
└── split-out/                 # Output directory
```

## Key Technologies

| Component | Version | Purpose |
|-----------|---------|---------|
| Gradle | 9.2.1 | Build orchestration |
| ANTLR4 | 4.13.2 | Parser generation |
| Python | 3.8+ | Runtime |
| Tkinter | Built-in | GUI framework |
| antlr4-python3-runtime | 4.13.2 | ANTLR runtime |
| requests | 2.31.0 | HTTP library |

## Build System

```bash
./gradlew build              # Setup everything  (downloads grammar, generates parsers, creates venv, installs deps)
./gradlew run                # Run the GUI
./gradlew test               # Run tests
./gradlew clean              # Clean artifacts
./gradlew generateGrammarSource  # Generate parsers only
```

## Features Implemented

- ✅ OpenQASM 3.0 parsing
- ✅ DQC pragma support
- ✅ Dynamic example loading (20+ from GitHub)
- ✅ Variable dependency analysis
- ✅ Interactive split point marking
- ✅ AST visualization
- ✅ Include file support
- ✅ Chunk export with annotations
- ✅ Distribute to worker nodes
- ✅ Cross-platform (Linux/macOS/Windows)
- ✅ Comprehensive test coverage

## Testing

10+ test suites covering:
- Installation and setup
- Grammar parsing
- GUI features
- Include file handling

Run with: `./gradlew test` or `python3 tests/run_all_tests.py`

## Documentation

- [README.md](README.md) - Complete guide with variable analysis explanation
- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup
- [DQC_GRAMMAR.md](DQC_GRAMMAR.md) - Pragma format specs
- [CONTROLLER_MODE_QUICKSTART.md](CONTROLLER_MODE_QUICKSTART.md) - Distributed execution

## Design Highlights

- **Modular architecture** - Parser, Analyzer, GUI as independent modules
- **Virtual environment** - Automatic isolated Python environment
- **Gradle integration** - Cross-language build orchestration
- **Professional documentation** - Quick start, detailed guides, specifications
- **Comprehensive testing** - 10+ test suites covering all features

