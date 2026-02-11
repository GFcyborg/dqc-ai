# Project Summary: DQC - OpenQASM Splitter

## Overview

A complete Python application with modular architecture for analyzing, visualizing, and splitting OpenQASM 3.0 quantum programs into distributed chunks. Built with Gradle orchestration of ANTLR4 parser generation and Python modules.

## What Has Been Created

### Build & Development Environment
- **Gradle-based build system** (version 9.2.1) as the primary orchestration tool
- **ANTLR4 4.13.2** for parsing OpenQASM 3.0 and DQC pragmas
- **Python virtual environment** setup with isolated dependencies
- **Cross-platform support** (Linux, macOS, Windows)

### Core Python Modules
1. **Parser Module** - OpenQASM 3.0 parsing with ANTLR4
2. **Analyzer Module** - Variable dependency analysis across code chunks
3. **GUI Module** - Interactive Tkinter-based graphical interface

### Features Implemented
- ✅ Dynamic example loading from GitHub (20+ examples)
- ✅ OpenQASM 3.0 grammar support
- ✅ DQC pragma grammar for split directives
- ✅ Variable declaration and usage tracking
- ✅ Complete type system (qubit, bit, int, float, angle, bool, complex, etc.)
- ✅ Interactive split point marking
- ✅ AST visualization
- ✅ Include directive support
- ✅ Chunk export with dependency comments
- ✅ Comprehensive test coverage

## Project Structure

```
dqc-ai/
├── 📋 Configuration & Documentation
│   ├── build.gradle              # Gradle build orchestration
│   ├── settings.gradle           # Gradle project settings
│   ├── gradle.properties         # Gradle properties
│   ├── requirements.txt          # Python dependencies
│   ├── .gitignore               # Git ignore rules
│   └── gradlew / gradlew.bat    # Gradle wrappers
│
├── 📖 Documentation
│   ├── README.md                 # Complete user guide
│   ├── QUICKSTART.md             # 5-minute setup guide
│   ├── PROJECT_SUMMARY.md        # This file
│   ├── DQC_GRAMMAR.md            # DQC pragma grammar specs
│   └── GUI_ENHANCEMENTS.md       # GUI feature documentation
│
├── 🚀 Entry Point
│   └── main.py                   # Main GUI application entry point
│
├── 💻 Source Code (src/main/python/)
│   ├── __init__.py
│   ├── stdlib.py                 # Standard library helper
│   │
│   ├── parser/                   # QASM Parsing Module
│   │   ├── __init__.py
│   │   ├── qasm_parser.py        # OpenQASM 3.0 parser wrapper
│   │   ├── dqc_parser.py         # DQC pragma parser wrapper
│   │   └── generated/            # ANTLR4-generated code
│   │       ├── qasm3Lexer.py
│   │       ├── qasm3Parser.py
│   │       ├── qasm3ParserVisitor.py
│   │       ├── dqcLexer.py
│   │       ├── dqcParser.py
│   │       └── dqcParserVisitor.py
│   │
│   ├── analyzer/                 # Variable Analysis Module
│   │   ├── __init__.py
│   │   └── variable_analyzer.py  # Dependency analyzer
│   │
│   └── gui/                      # GUI Module
│       ├── __init__.py
│       └── main_window.py        # Tkinter-based interface
│
├── 📝 Grammar Files (src/main/antlr4/)
│   ├── qasm3Lexer.g4            # OpenQASM 3.0 lexer (auto-downloaded)
│   ├── qasm3Parser.g4           # OpenQASM 3.0 parser (auto-downloaded)
│   ├── dqcLexer.g4              # DQC pragma lexer
│   └── dqcParser.g4             # DQC pragma parser
│
├── 🧪 Test Suites (tests/)
│   ├── run_all_tests.py         # Main test runner
│   ├── test_installation.py     # Setup verification
│   ├── test_dqc_grammar.py      # DQC grammar tests
│   ├── test_dqc_wrapper.py      # DQC parser tests
│   ├── test_gui_enhancements.py # GUI feature tests
│   ├── test_includes.py         # Include directive tests
│   ├── test_include_tabs.py     # Include tab management tests
│   ├── test_include_download.py # Include file download tests
│   └── test_save_includes.py    # Include file save tests
│
└── 📦 Output
    └── split-out/               # Chunk export directory
        └── (example chunks)
```

## Core Modules Overview

### 1. Parser Module (`src/main/python/parser/`)

**Purpose**: Parse OpenQASM 3.0 and DQC pragmas

**Key Files**:
- `qasm_parser.py` - OpenQASM 3.0 parser wrapper
  - `QasmParser` class for parsing `.qasm` files
  - `ParseResult` for containing parse results
  - Error collection and reporting
  
- `dqc_parser.py` - DQC pragma parser wrapper
  - Recognizes `pragma dqc.vX.split id=N` directives
  - Extracts split point identifiers

**Technology**: ANTLR4 4.13.2 with Python target

### 2. Analyzer Module (`src/main/python/analyzer/`)

**Purpose**: Analyze variable dependencies and track their usage

**Key Functionality**:
- Variable declaration tracking across chunks
- Complete OpenQASM type system support
- Usage analysis per code section
- Dependency resolution between chunks
- `VariableInfo` - Metadata (name, type, size, definition line)
- `ChunkInfo` - Chunk data and required variables
- `VariableAnalyzer` - Main analysis engine

**Supported Types**:
- `qubit`, `bit` - Quantum and classical bits
- `int`, `uint` - Signed and unsigned integers
- `float` - Floating-point numbers
- `angle` - Rotation angles
- `bool` - Boolean values
- `complex` - Complex numbers
- `duration` - Time durations
- `stretch` - Timing stretches
- Arrays with size notation: `qubit[5]`, `bit[10]`, etc.

### 3. GUI Module (`src/main/python/gui/`)

**Purpose**: Interactive graphical interface for analyzing and splitting programs

**Key Features**:
- **File Management**
  - Load local QASM files
  - Dynamically load examples from GitHub (20+ examples)
  - Handle include directives automatically
  
- **Source Code Display**
  - Perfectly aligned line numbers (shared font)
  - Monospace character display
  - Readable layout
  
- **Analysis Tabs**
  - Source Code - View QASM with line numbers
  - AST View - Visualize Abstract Syntax Tree
  - Variable Analysis - View detected variables and dependencies
  
- **Chunk Operations**
  - Mark split points by clicking lines
  - Analyze dependencies per chunk
  - Export chunks as individual files
  
- **GitHub Integration**
  - Automatic example discovery
  - Online file caching
  - Fallback to local files

**Technology**: Tkinter (Python standard library) for cross-platform compatibility

## Key Technologies

| Tool | Version | Purpose |
|------|---------|---------|
| Gradle | 9.2.1 | Build orchestration |
| ANTLR4 | 4.13.2 | Parser generation |
| Python | 3.8+ | Runtime |
| Tkinter | Built-in | GUI framework |
| antlr4-python3-runtime | 4.13.2 | ANTLR runtime |
| requests | 2.31.0 | HTTP library |
| Java | 8+ | ANTLR compilation |

## Build System Overview

### Gradle Task Hierarchy

```
build (default)
├── setup
│   ├── setupPythonEnv
│   └── generateGrammarSource
│       ├── generateQASM3Parsers
│       └── generateDQCParsers
│           └── downloadGrammar
│
run
├── build (ensures everything is built)
│
test
├── setup (ensures dependencies installed)
│
clean
├── cleanGrammar
└── cleanPython
```

### Build Commands

**Full Build**: `./gradlew build`
- One command to setup everything from scratch
- Handles grammar download, parser generation, venv creation

**Run Application**: `./gradlew run` 
- Builds if needed
- Launches GUI with virtual environment Python

**Test**: `./gradlew test`
- Runs all Python test suites
- Uses virtual environment Python

**Clean**: `./gradlew clean`
- Removes all generated files and intermediate artifacts
- Includes subcommands:
  - `cleanGrammar` - Remove ANTLR-generated files
  - `cleanPython` - Remove venv and Python cache

## Installation & Setup

### Quick Setup
```bash
./gradlew build    # Complete one-time setup
./gradlew run      # Run the application
```

### What Happens During `./gradlew build`:

1. **Check/Create Virtual Environment**
   - Creates `.venv/` if it doesn't exist
   - Isolated Python environment per project

2. **Download OpenQASM Grammar**
   - Fetches official grammar from OpenQASM repository
   - Caches in `src/main/antlr4/`

3. **Generate Parsers**
   - QASM3 parser from grammar
   - DQC pragma parser
   - Output to `src/main/python/parser/generated/`

4. **Install Dependencies**
   - antlr4-python3-runtime for ANTLR support
   - requests for downloading examples
   - Installed in virtual environment

5. **Verify Setup**
   - Ensures all components are ready
   - Reports any issues

## Testing Infrastructure

### Test Suites
- **test_installation.py** - Verify build artifacts and dependencies
- **test_dqc_grammar.py** - DQC pragma parsing
- **test_dqc_wrapper.py** - DQC parser wrapper functionality
- **test_gui_enhancements.py** - GUI features (alignment, example loading)
- **test_includes.py** - Include directive handling
- **test_include_tabs.py** - Include file tab management
- **test_include_download.py** - GitHub include file downloading
- **test_save_includes.py** - Exporting include files

### Running Tests
```bash
./gradlew test          # Using Gradle
python3 tests/run_all_tests.py  # Direct execution
```

## Feature Highlights

### ✅ Dynamic Example Loading
- Fetches list from GitHub API
- Shows 20+ official OpenQASM examples
- Seamless download and caching

### ✅ Variable Dependency Analysis
- Automatic tracking of all variable usage
- Identifies which variables each chunk needs
- Comment annotations in exported chunks

### ✅ Cross-Platform Compatibility
- Linux/macOS/Windows support
- Same build process everywhere
- Tkinter GUI works on all platforms

### ✅ Comprehensive Type Support
- All OpenQASM 3.0 types
- Array declarations with sizes
- Complex and duration types

### ✅ Professional Documentation
- Detailed README
- Quick start guide
- Grammar specifications
- Feature documentation

## Design Decisions

1. **Gradle as Build Tool**
   - Single entry point for all operations
   - Handles multi-language build complexity
   - Reliable virtual environment management

2. **Tkinter for GUI**
   - No external dependencies required
   - Built into Python
   - Simple, maintainable codebase
   - Cross-platform compatibility

3. **ANTLR4 for Parsing**
   - Industrial-strength parser generator
   - Direct grammar support from OpenQASM
   - Proven and widely-used technology

4. **Modular Architecture**
   - Clear separation of concerns
   - Parser, Analyzer, GUI as independent modules
   - Easy to test and extend

5. **Virtual Environment by Default**
   - Automatic venv creation
   - Isolated dependencies
   - No system-wide Python pollution
   - Reliable dependency management

## Future Enhancement Opportunities

- Web-based GUI (Flask/Django)
- Additional quantum frameworks support
- Performance optimization for large files
- Advanced visualizations
- Community plugin system
- Cloud-based execution coordination

## Conclusion

This project demonstrates a complete, professional-grade quantum program analysis tool built with modern development practices. It showcases:
- Effective integration of build tools and languages
- Comprehensive testing and documentation
- User-friendly GUI design
- Sound architectural decisions
- Production-ready code quality
