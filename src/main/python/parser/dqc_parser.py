"""
DQC Parser wrapper for recognizing DQC pragma lines
"""

import sys
import os
import re
from dataclasses import dataclass
from typing import List, Optional

# Add generated parser directory to path
# Try build directory first, then fall back to legacy location
GENERATED_DIRS = [
    os.path.join(os.path.dirname(__file__), '../../../../build/generated-sources/python'),
    os.path.join(os.path.dirname(__file__), 'generated'),  # legacy location
]

GENERATED_DIR = None
for dir_path in GENERATED_DIRS:
    if os.path.exists(dir_path):
        GENERATED_DIR = dir_path
        sys.path.insert(0, GENERATED_DIR)
        break

if GENERATED_DIR is None:
    DQC_PARSERS_AVAILABLE = False
else:
    DQC_PARSERS_AVAILABLE = True

try:
    from antlr4 import InputStream, CommonTokenStream
    from dqcLexer import dqcLexer
    from dqcParser import dqcParser
except ImportError:
    DQC_PARSERS_AVAILABLE = False
    print("Warning: DQC parsers not available. Run './gradlew generateDQCGrammar' first.")


@dataclass
class DQCPragma:
    """Represents a DQC pragma directive"""
    version: int
    split_id: int
    line_number: int
    raw_text: str


class DQCPragmaParser:
    """Parser for DQC pragma directives in .dqc files"""
    
    # Regex pattern for DQC pragmas (flexible with whitespace, id must be >= 1)
    PRAGMA_PATTERN = re.compile(r'pragma\s+dqc\s*\.\s*v(\d+)\s*\.\s*split\s+id\s*=\s*([1-9]\d*)')
    
    def __init__(self):
        if not DQC_PARSERS_AVAILABLE:
            raise RuntimeError(
                "DQC parsers not available. Please run:\n"
                "  ./gradlew generateDQCGrammar"
            )
    
    def parse_file(self, filepath: str) -> List[DQCPragma]:
        """
        Parse a .dqc file and extract all DQC pragma directives
        
        Args:
            filepath: Path to the .dqc file
            
        Returns:
            List of DQCPragma objects
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse_string(content)
    
    def parse_string(self, content: str) -> List[DQCPragma]:
        """
        Parse content and extract all DQC pragma directives
        
        Args:
            content: String content to parse
            
        Returns:
            List of DQCPragma objects
            
        Note:
            Split IDs are validated by the regex pattern to be >= 1
            (pattern: [1-9][0-9]*, which matches 1, 2, 3, ... but not 0)
        """
        pragmas = []
        
        for line_num, line in enumerate(content.split('\n'), start=1):
            match = self.PRAGMA_PATTERN.search(line)
            if match:
                version = int(match.group(1))
                split_id = int(match.group(2))
                
                # Note: split_id is guaranteed to be >= 1 by the regex pattern
                # (matches [1-9][0-9]*), but we double-check for safety
                if split_id < 1:
                    raise ValueError(
                        f"Line {line_num}: Split ID must be >= 1 (found {split_id}). "
                        f"ID 0 is reserved for the implicit initial chunk."
                    )
                
                pragmas.append(DQCPragma(
                    version=version,
                    split_id=split_id,
                    line_number=line_num,
                    raw_text=line.strip()
                ))
        
        return pragmas
    
    @staticmethod
    def validate_pragma_sequence(pragmas: List[DQCPragma]) -> tuple[bool, Optional[str]]:
        """
        Validate that pragma split IDs form a proper sequence
        
        Args:
            pragmas: List of DQCPragma objects
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not pragmas:
            return True, None
        
        # Check that IDs start from 1 and are sequential
        split_ids = sorted([p.split_id for p in pragmas])
        
        if split_ids[0] != 1:
            return False, f"Split IDs must start from 1 (found {split_ids[0]})"
        
        for i in range(1, len(split_ids)):
            if split_ids[i] != split_ids[i-1] + 1:
                return False, f"Split IDs must be sequential (gap between {split_ids[i-1]} and {split_ids[i]})"
        
        return True, None
