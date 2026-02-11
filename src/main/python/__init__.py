"""
DQC - OpenQASM Splitter

A tool for analyzing OpenQASM 3.0 programs, visualizing their AST,
and splitting them into chunks with automatic variable dependency analysis.
"""

__version__ = '1.0.0'
__author__ = 'DQC-AI Team'

from . import parser
from . import analyzer
from . import gui
from . import choreo

__all__ = ['parser', 'analyzer', 'gui', 'choreo']
