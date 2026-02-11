"""
Variable dependency analyzer for OpenQASM code
"""

import re
from dataclasses import dataclass, field
from typing import List, Set, Dict, Tuple, Optional


@dataclass
class VariableInfo:
    """Information about a variable"""
    name: str
    type: str  # 'qubit', 'bit', 'int', 'float', 'angle', etc.
    size: int = 1  # For arrays
    defined_at: int = -1  # Line number where defined
    
    def __str__(self):
        if self.size > 1:
            return f"{self.type}[{self.size}] {self.name}"
        return f"{self.type} {self.name}"


@dataclass
class ChunkInfo:
    """Information about a code chunk"""
    start_line: int
    end_line: int
    required_variables: List[VariableInfo] = field(default_factory=list)
    source_lines: List[str] = field(default_factory=list)


class VariableAnalyzer:
    """
    Analyzes OpenQASM code to track variable definitions, usages, and types
    """
    
    # OpenQASM 3.0 type keywords
    QASM_TYPES = {
        'qubit', 'bit', 'int', 'uint', 'float', 'angle', 
        'bool', 'duration', 'stretch', 'complex'
    }
    
    def __init__(self):
        self.variables: Dict[str, VariableInfo] = {}
        self.source_lines: List[str] = []
    
    def analyze(self, source_code: str, split_points: List[int]) -> List[ChunkInfo]:
        """
        Analyze source code and determine variable dependencies for each chunk
        
        Args:
            source_code: The QASM source code
            split_points: List of 1-indexed line numbers where new chunks should START
            
        Returns:
            List of ChunkInfo objects, one for each chunk
        """
        self.source_lines = source_code.splitlines()
        self.variables = {}
        
        # Convert 1-indexed split points to 0-indexed boundaries
        # User clicks line 5 (1-indexed) means "start new chunk at line 5"
        # In 0-indexed terms, that's index 4
        split_points_0indexed = [sp - 1 for sp in split_points]
        
        # Sort split points and add boundaries
        split_points_0indexed = sorted(set([0] + split_points_0indexed + [len(self.source_lines)]))
        
        # Sort split points and add boundaries
        split_points_0indexed = sorted(set([0] + split_points_0indexed + [len(self.source_lines)]))
        
        # First pass: find all variable declarations
        self._find_declarations()
        
        # Second pass: analyze each chunk
        chunks = []
        for i in range(len(split_points_0indexed) - 1):
            start = split_points_0indexed[i]
            end = split_points_0indexed[i + 1]
            chunk = self._analyze_chunk(start, end)
            chunks.append(chunk)
        
        return chunks
    
    def _find_declarations(self):
        """First pass: find all variable declarations in the code"""
        for line_num, line in enumerate(self.source_lines, start=1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('//'):
                continue
            
            # Check for variable declarations
            self._extract_declarations(line, line_num)
    
    def _extract_declarations(self, line: str, line_num: int):
        """Extract variable declarations from a line"""
        # Pattern for type declarations: type name or type[size] name
        # Examples:
        #   qubit q;
        #   qubit[5] qubits;
        #   int[32] result;
        #   bit[10] measurements;
        
        for qasm_type in self.QASM_TYPES:
            # Pattern: type[size] name or type name
            pattern = rf'\b{qasm_type}(\[(\d+)\])?\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            matches = re.finditer(pattern, line)
            
            for match in matches:
                size_str = match.group(2)
                var_name = match.group(3)
                
                size = int(size_str) if size_str else 1
                
                self.variables[var_name] = VariableInfo(
                    name=var_name,
                    type=qasm_type,
                    size=size,
                    defined_at=line_num
                )
        
        # Also check for gate definitions (custom gates)
        gate_match = re.search(r'\bgate\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
        if gate_match:
            gate_name = gate_match.group(1)
            self.variables[gate_name] = VariableInfo(
                name=gate_name,
                type='gate',
                size=1,
                defined_at=line_num
            )
    
    def _analyze_chunk(self, start_line: int, end_line: int) -> ChunkInfo:
        """
        Analyze a chunk to determine which variables it needs
        
        Args:
            start_line: Starting line number (0-indexed)
            end_line: Ending line number (exclusive, 0-indexed)
            
        Returns:
            ChunkInfo with required variables
        """
        chunk = ChunkInfo(
            start_line=start_line + 1,  # Convert to 1-indexed for display
            end_line=end_line,  # end_line is exclusive in slicing, so last line included is end_line-1 in 0-indexed, which is end_line in 1-indexed display
            source_lines=self.source_lines[start_line:end_line]
        )
        
        # Find all variables used in this chunk
        used_vars = set()
        defined_in_chunk = set()
        
        for line in chunk.source_lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('//'):
                continue
            
            # Find variables defined in this chunk
            for var_name in self.variables.keys():
                if self._is_declaration(line, var_name):
                    defined_in_chunk.add(var_name)
            
            # Find variables used in this chunk
            for var_name in self.variables.keys():
                if self._is_used(line, var_name):
                    used_vars.add(var_name)
        
        # Required variables are those used but not defined in this chunk
        required_var_names = used_vars - defined_in_chunk
        
        # Filter to only include variables defined before this chunk
        chunk.required_variables = [
            self.variables[var_name]
            for var_name in required_var_names
            if self.variables[var_name].defined_at < start_line + 1
        ]
        
        # Sort by line where defined
        chunk.required_variables.sort(key=lambda v: v.defined_at)
        
        return chunk
    
    def _is_declaration(self, line: str, var_name: str) -> bool:
        """Check if a line declares the given variable"""
        var_info = self.variables.get(var_name)
        if not var_info:
            return False
        
        # Check if this line contains a declaration for this variable
        for qasm_type in self.QASM_TYPES:
            pattern = rf'\b{qasm_type}(\[\d+\])?\s+{re.escape(var_name)}\b'
            if re.search(pattern, line):
                return True
        
        # Check for gate definition
        if var_info.type == 'gate':
            pattern = rf'\bgate\s+{re.escape(var_name)}\b'
            if re.search(pattern, line):
                return True
        
        return False
    
    def _is_used(self, line: str, var_name: str) -> bool:
        """Check if a variable is used in a line"""
        # Simple heuristic: check if variable name appears as a word boundary
        pattern = rf'\b{re.escape(var_name)}\b'
        return bool(re.search(pattern, line))
    
    def get_variable_info(self, var_name: str) -> Optional[VariableInfo]:
        """Get information about a specific variable (or None if not found)"""
        return self.variables.get(var_name)
    
    def get_all_variables(self) -> List[VariableInfo]:
        """Get all tracked variables"""
        return list(self.variables.values())
