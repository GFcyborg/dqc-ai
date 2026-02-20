#!/usr/bin/env python3
"""
Choreo module entry point - allows running as: python -m choreo.worker

This module serves as a dispatcher for CLI commands within the choreo package.
"""

import sys
import importlib


def main():
    """Route CLI commands to appropriate submodules."""
    if len(sys.argv) < 2:
        print("Usage: python -m choreo.<command> [args]")
        print("  Commands:")
        print("    python -m choreo.worker <port> [--host HOST] [--output-dir DIR]")
        print("    python -m choreo.controller <input_dir> [--config CONFIG]")
        sys.exit(1)
    
    # The module name is passed in sys.argv[0] when run with -m
    # We just need to delegate to the appropriate submodule's main()
    print("Note: Use 'python -m choreo.worker' or 'python -m choreo.controller' directly")
    sys.exit(0)


if __name__ == "__main__":
    main()
