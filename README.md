# DQC - OpenQASM Splitter

A comprehensive Python application for analyzing OpenQASM 3.0 programs, visualizing their Abstract Syntax Trees (AST), and splitting quantum code into distributed chunks with automatic variable dependency analysis.

## Overview

DQC (Distributed Quantum Computing) is a tool designed to help break down large quantum programs into manageable chunks for distributed execution. It leverages ANTLR4 to parse OpenQASM 3.0 syntax and provides an interactive GUI for marking split points and analyzing variable dependencies.

## Features

- **OpenQASM 3.0 Support**: Full parser support for the latest OpenQASM specification
- **Dynamic Example Loading**: Access 20+ official OpenQASM examples directly from GitHub
- **Interactive Source Viewer**: View QASM code with perfectly aligned line numbers
- **AST Visualization**: Parse and visualize Abstract Syntax Trees using ANTLR4
- **Split Point Marking**: Click on code lines to mark splitting boundaries
- **Variable Dependency Analysis**: Automatically determine which variables are needed for each chunk
- **Type Tracking**: Recognize all OpenQASM types (qubit, bit, int, float, angle, bool, complex, etc.)
- **Chunk Export**: Save code chunks as separate `.qasm` files with dependency annotations
- **DQC Pragma Support**: Recognize DQC pragma directives for marking split points
- **Include File Support**: Handle OpenQASM `include` directives and manage standard library files
- **Cross-Platform**: Works on Linux, macOS, and Windows

## Requirements

- **Python**: 3.8 or later
- **Java**: 8 or later (required for Gradle and ANTLR4 parser generation)
- **Gradle**: 9.2.1 (provided via included gradle wrapper)

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd dqc-ai
```

### 2. Build and Generate Parsers

```bash
./gradlew build
```

This single command will:
- Download OpenQASM grammar files from the official repository
- Generate QASM3 and DQC ANTLR4 parsers
- Create a Python virtual environment
- Install all dependencies (`antlr4-python3-runtime`, `requests`)

### 3. Run the Application

```bash
./gradlew run
```

This will start the interactive GUI application.

## Installation Details

### Complete Build Process

The `./gradlew build` command performs the following steps:

1. **Download OpenQASM Grammar**
   - Fetches `qasm3Lexer.g4` and `qasm3Parser.g4` from the official OpenQASM repository
   - Stores them in `src/main/antlr4/`

2. **Generate QASM3 Parsers**
   - Generates Python parser code from the OpenQASM grammar files
   - Output: `src/main/python/parser/generated/qasm3Lexer.py`, `qasm3Parser.py`, etc.

3. **Generate DQC Parsers**
   - Generates parsers for DQC pragma directives (format: `pragma dqc.vX.split id=N`)
   - Output: `src/main/python/parser/generated/dqcLexer.py`, `dqcParser.py`, etc.

4. **Create Python Virtual Environment**
   - Creates `.venv/` directory with isolated Python environment

5. **Install Python Dependencies**
   - `antlr4-python3-runtime==4.13.2` - ANTLR4 Python runtime
   - `requests==2.31.0` - HTTP library for downloading examples

### Manual Setup (if needed)

If you prefer manual setup:

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install -r requirements.txt

# Generate parsers
./gradlew generateGrammarSource  # Generates QASM3 and DQC parsers
```

## Usage

### Running the Application

```bash
./gradlew run
```

### Using the GUI Application

The GUI provides an intuitive interface with the following tabs and features:

**File Menu:**
- **Open Local File**: Load a `.qasm` file from your filesystem
- **Load Example**: Access 20+ official OpenQASM examples
  - Adder, Alignment, Arrays, Cphase, DD, Defcal, Gateteleport
  - Inverseqft1, Inverseqft2, Ipe, MSD, QEC, QFT, QPT
  - RB, RUS, SCQEC, T1, Teleport, Varteleport, VQE
  - (Dynamically loaded from GitHub)

**Program Tabs:**
- **Source Code**: View your QASM code with synchronized line numbers
- **AST View**: See the parsed Abstract Syntax Tree
- **Variable Analysis**: View detected variables and their dependencies per chunk

**Splitting Workflow:**
1. Load a QASM file (local or example)
2. Click on source code lines to mark split points
3. Review variables in the "Variable Analysis" tab
4. Click "Analyze & Save Chunks" to export

## Project Structure

```
dqc-ai/
├── build.gradle              # Gradle build configuration
├── settings.gradle           # Gradle settings
├── gradle.properties         # Gradle properties
├── requirements.txt          # Python dependencies
├── main.py                   # Main entry point
├── README.md                 # This file
├── QUICKSTART.md             # Quick start guide
├── PROJECT_SUMMARY.md        # Project overview
├── DQC_GRAMMAR.md            # DQC pragma grammar documentation
├── GUI_ENHANCEMENTS.md       # GUI enhancement documentation
├── gradlew                   # Gradle wrapper (Linux/Mac)
├── gradlew.bat              # Gradle wrapper (Windows)
│
├── src/main/
│   ├── antlr4/              # ANTLR4 grammar files
│   │   ├── qasm3Lexer.g4    # OpenQASM 3.0 lexer (downloaded)
│   │   ├── qasm3Parser.g4   # OpenQASM 3.0 parser (downloaded)
│   │   ├── dqcLexer.g4      # DQC pragma lexer
│   │   └── dqcParser.g4     # DQC pragma parser
│   │
│   └── python/              # Python source code
│       ├── __init__.py
│       ├── stdlib.py        # Standard library helper
│       ├── parser/          # QASM parsing module
│       │   ├── __init__.py
│       │   ├── qasm_parser.py      # OpenQASM parser wrapper
│       │   ├── dqc_parser.py       # DQC pragma parser wrapper
│       │   └── generated/          # ANTLR4-generated parsers
│       │       ├── qasm3Lexer.py
│       │       ├── qasm3Parser.py
│       │       ├── qasm3ParserVisitor.py
│       │       ├── dqcLexer.py
│       │       ├── dqcParser.py
│       │       └── dqcParserVisitor.py
│       │
│       ├── analyzer/        # Variable analysis module
│       │   ├── __init__.py
│       │   └── variable_analyzer.py  # Dependency analyzer
│       │
│       └── gui/             # GUI module
│           ├── __init__.py
│           └── main_window.py       # Main GUI window (Tkinter)
│
├── tests/                   # Test suites
│   ├── run_all_tests.py     # Main test runner
│   ├── test_installation.py # Installation verification
│   ├── test_dqc_grammar.py  # DQC grammar tests
│   ├── test_dqc_wrapper.py  # DQC parser wrapper tests
│   ├── test_gui_enhancements.py # GUI feature tests
│   ├── test_includes.py     # Include directive tests
│   ├── test_include_tabs.py # Include tab tests
│   ├── test_include_download.py # Include download tests
│   └── test_save_includes.py # Include save tests
│
└── split-out/              # Output directory for chunk splitting
    └── (example chunks saved here)
```

## Modules

### 1. Parser Module (`src/main/python/parser/`)

Handles OpenQASM 3.0 and DQC pragma parsing using ANTLR4:
- **qasm_parser.py**: Wrapper for OpenQASM 3.0 parsing
  - `QasmParser`: Main parser class
  - `ParseResult`: Container for parse results
  - Supports AST visualization and error reporting
  
- **dqc_parser.py**: Wrapper for DQC pragma parsing
  - Recognizes split point pragmas: `pragma dqc.vX.split id=N`
  - Extracts pragma IDs for program splitting

### 2. Analyzer Module (`src/main/python/analyzer/`)

Analyzes variable dependencies across code chunks:
- **variable_analyzer.py**: 
  - `VariableAnalyzer`: Tracks variable declarations and usage
  - `VariableInfo`: Stores variable metadata (name, type, size, definition line)
  - `ChunkInfo`: Stores chunk information and required variables
  - Type tracking for all OpenQASM 3.0 types
  - Recursive analysis for chunks and dependencies

### 3. GUI Module (`src/main/python/gui/`)

Provides the interactive graphical interface:
- **main_window.py**:
  - `QasmAnalyzerGUI`: Main window class
  - Dynamic example loading from GitHub API
  - Synchronized line numbers and source code display
  - Include file tab management
  - AST visualization
  - Variable analysis display
  - Chunk export functionality
  - Tkinter-based for cross-platform compatibility

### 4. Standard Library Module (`src/main/python/stdlib.py`)

Helper module for accessing OpenQASM standard library files from the official repository.

## Supported OpenQASM Types

The analyzer recognizes these OpenQASM 3.0 types:
- `qubit` - Quantum bits
- `bit` - Classical bits
- `int`, `uint` - Integers
- `float` - Floating-point numbers
- `angle` - Rotation angles
- `bool` - Boolean values
- `duration` - Time durations
- `stretch` - Timing stretch
- `complex` - Complex numbers

Arrays are supported with size notation: `qubit[5]`, `bit[10]`, etc.

## Gradle Tasks

The project uses Gradle as its build system. Available tasks:

```bash
./gradlew build                # Complete build (default task)
./gradlew run                  # Run the GUI application
./gradlew test                 # Run all tests
./gradlew clean                # Clean all build artifacts
./gradlew cleanGrammar         # Clean only ANTLR-generated files
./gradlew cleanPython          # Clean only Python virtual environment and cache
./gradlew generateGrammarSource # Generate QASM3 and DQC parsers
./gradlew setupPythonEnv       # Setup Python virtual environment and dependencies
```

## Testing

Run all tests with:

```bash
./gradlew test
```

Or run tests directly:

```bash
python3 tests/run_all_tests.py
```

Individual test suites:
- `test_installation.py` - Verify installation and dependencies
- `test_dqc_grammar.py` - Test DQC pragma parsing
- `test_dqc_wrapper.py` - Test DQC parser wrapper
- `test_gui_enhancements.py` - Test GUI features
- `test_includes.py` - Test include directive handling
- `test_include_tabs.py` - Test include file tab management
- `test_include_download.py` - Test include file downloads
- `test_save_includes.py` - Test include file saving

## Troubleshooting

### "Parser not available" error
- Run `./gradlew build` to generate the parsers
- Ensure Java 8+ is installed
- Check that internet connection is available for downloading grammar files

### "ModuleNotFoundError: No module named 'antlr4'"
- Run `./gradlew build` to install dependencies
- Or manually install: `pip install antlr4-python3-runtime==4.13.2`

### Grammar download fails
- Check your internet connection
- Manually download grammar files from: https://github.com/openqasm/openqasm/tree/main/source/grammar
- Place them in `src/main/antlr4/`

### "No such file or directory: .venv/bin/python3" (Linux/Mac)
- The virtual environment needs to be created by running `./gradlew build`
- Do not move the project directory after building

### GUI doesn't start
- Ensure Tkinter is installed (on Linux: `sudo apt-get install python3-tk`)
- Check that the virtual environment was created: `ls -la .venv/`
- Try running manually: `.venv/bin/python3 main.py` (or `./gradlew run`)

### Can't download examples from GitHub
- Check your internet connection
- Try accessing https://github.com/openqasm/openqasm/tree/main/examples in your browser
- Use "Open Local File" to load QASM files instead

## Gradle Wrapper

The project includes Gradle wrapper scripts (`gradlew` and `gradlew.bat`) that automatically download and run the correct Gradle version. You don't need to install Gradle separately.

## Technical Details

- **Build Tool**: Gradle 9.2.1 (Groovy-based build script)
- **Parser Generator**: ANTLR4 4.13.2
- **Python Runtime**: 3.8+
- **Python Dependencies**: 
  - `antlr4-python3-runtime==4.13.2` - ANTLR4 parser runtime
  - `requests==2.31.0` - HTTP library for example downloads
- **GUI Framework**: Tkinter (built into Python)
- **OpenQASM Version**: 3.0
- **DQC Version**: 1.0 (pragma format: `pragma dqc.v1.split id=N`)

## Project Development

This project was developed as part of a thesis on distributed quantum computing. It demonstrates:
- Integration of ANTLR4 grammar-based parsing with Python
- Gradle-based build orchestration for multi-language projects
- Cross-platform GUI development with Tkinter
- Variable dependency analysis for quantum programs
- OpenQASM 3.0 language support

## License

This project uses the OpenQASM grammar from the official OpenQASM repository.
OpenQASM is developed by the OpenQASM community and Qiskit team.

## References

- **OpenQASM Repository**: https://github.com/openqasm/openqasm
- **OpenQASM Specification**: https://openqasm.com/
- **ANTLR4 Documentation**: https://www.antlr.org/
- **Gradle Documentation**: https://gradle.org/


**"Parser not available" error**:
- Run `gradle generateGrammarSource` to generate the parsers
- Make sure Java and Gradle are installed

**"ModuleNotFoundError: No module named 'antlr4'"**:
- Run `pip install -r requirements.txt`

**Grammar download fails**:
- Check your internet connection
- Manually download grammar files from:
  - https://github.com/openqasm/openqasm/tree/main/source/grammar
- Place them in `src/main/antlr4/`

## Technical Details

- **Build Tool**: Gradle 9.2.1 (Groovy-based build script)
- **Parser Generator**: ANTLR4 4.13.2
- **Python Runtime**: antlr4-python3-runtime 4.13.2
- **GUI Framework**: Tkinter (built into Python)
- **OpenQASM Version**: 3.0

## License

This project uses the OpenQASM grammar from the official OpenQASM repository.
OpenQASM is developed by the OpenQASM community and Qiskit team.

## References

- OpenQASM Repository: https://github.com/openqasm/openqasm
- OpenQASM Specification: https://openqasm.com/
- ANTLR4 Documentation: https://www.antlr.org/
