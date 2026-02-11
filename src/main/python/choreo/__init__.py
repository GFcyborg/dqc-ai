"""
Choreo: Controller-Worker Orchestration System

A multi-node orchestration system for distributed quantum circuit processing.
Supports both CLI usage and direct Python imports.

Architecture:
  - Controller: Coordinates task distribution to worker nodes
  - Worker: Receives and processes distributed tasks
  - Protocol: Binary file transfer protocol for task communication
"""

__version__ = '1.0.0'
__author__ = 'DQC-AI Team'

from .controller import Controller
from .worker import Worker

__all__ = ['Controller', 'Worker']
