#!/usr/bin/env python3
"""
Main entry point for the DQC - OpenQASM Splitter GUI

Usage:
    python main.py
"""

import sys
import os

# Add src/main/python to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'main', 'python'))

import tkinter as tk
from gui import QasmAnalyzerGUI


def main():
    """Main entry point"""
    root = tk.Tk()
    app = QasmAnalyzerGUI(root)
    app.run()


if __name__ == '__main__':
    main()
