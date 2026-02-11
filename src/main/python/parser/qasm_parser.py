"""
QASM Parser wrapper for ANTLR4 generated parsers
"""

import sys
import os
from dataclasses import dataclass
from typing import Optional, List, Any

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
    PARSERS_AVAILABLE = False
else:
    PARSERS_AVAILABLE = True

try:
    from antlr4 import *
    from qasm3Lexer import qasm3Lexer
    from qasm3Parser import qasm3Parser
except ImportError:
    PARSERS_AVAILABLE = False
    print("Warning: ANTLR4 parsers not available. Run './gradlew generateGrammarSource' first.")


@dataclass
class ParseResult:
    """Container for parse results"""
    source_code: str
    parse_tree: Optional[Any] = None
    ast: Optional[Any] = None
    errors: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class QasmParser:
    """Parser for OpenQASM 3.0 files using ANTLR4"""
    
    def __init__(self):
        if not PARSERS_AVAILABLE:
            raise RuntimeError(
                "ANTLR4 parsers not available. Please run:\n"
                "  gradle generateGrammarSource\n"
                "  pip install -r requirements.txt"
            )
    
    def parse_file(self, filepath: str) -> ParseResult:
        """
        Parse an OpenQASM file
        
        Args:
            filepath: Path to the .qasm file
            
        Returns:
            ParseResult containing source code, parse tree, and AST
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        return self.parse_string(source_code)
    
    def parse_string(self, source_code: str) -> ParseResult:
        """
        Parse OpenQASM source code string
        
        Args:
            source_code: QASM source code
            
        Returns:
            ParseResult containing parse tree and AST
        """
        result = ParseResult(source_code=source_code)
        
        try:
            # Create lexer and token stream
            input_stream = InputStream(source_code)
            lexer = qasm3Lexer(input_stream)
            token_stream = CommonTokenStream(lexer)
            
            # Create parser
            parser = qasm3Parser(token_stream)
            
            # Custom error listener
            error_listener = ErrorListener()
            parser.removeErrorListeners()
            parser.addErrorListener(error_listener)
            
            # Parse the program
            parse_tree = parser.program()
            
            result.parse_tree = parse_tree
            result.ast = self._build_ast(parse_tree, source_code)
            result.errors = error_listener.errors
            
        except Exception as e:
            result.errors.append(f"Parse error: {str(e)}")
        
        return result
    
    def _build_ast(self, parse_tree, source_code: str) -> Optional[dict]:
        """
        Build a simplified AST representation from the parse tree
        
        Args:
            parse_tree: ANTLR4 parse tree
            source_code: Original source code to extract text with whitespace
            
        Returns:
            Dictionary representation of the AST (or None)
        """
        if parse_tree is None:
            return None
        
        # Get rule name
        rule_name = qasm3Parser.ruleNames[parse_tree.getRuleIndex()] if hasattr(parse_tree, 'getRuleIndex') else 'terminal'
        
        # Extract actual text from source code using token positions to preserve whitespace
        if hasattr(parse_tree, 'start') and hasattr(parse_tree, 'stop') and parse_tree.stop is not None:
            start_idx = parse_tree.start.start
            stop_idx = parse_tree.stop.stop
            text = source_code[start_idx:stop_idx + 1]
        else:
            text = parse_tree.getText() if hasattr(parse_tree, 'getText') else str(parse_tree)
        
        ast_node = {
            'type': rule_name,
            'text': text,
        }
        
        # Add line information if available
        if hasattr(parse_tree, 'start'):
            ast_node['line'] = parse_tree.start.line
            ast_node['column'] = parse_tree.start.column
        
        # Recursively process children
        if hasattr(parse_tree, 'getChildCount'):
            children = []
            for i in range(parse_tree.getChildCount()):
                child = parse_tree.getChild(i)
                if child is not None:
                    child_ast = self._build_ast(child, source_code)
                    if child_ast:
                        children.append(child_ast)
            
            if children:
                ast_node['children'] = children
        
        return ast_node
    
    @staticmethod
    def format_ast(ast: dict, indent: int = 0) -> str:
        """
        Format AST as a readable string
        
        Args:
            ast: AST dictionary
            indent: Current indentation level
            
        Returns:
            Formatted string representation
        """
        if ast is None:
            return ""
        
        lines = []
        prefix = "  " * indent
        
        # Format current node
        node_info = f"{prefix}{ast['type']}"
        if 'line' in ast:
            node_info += f" (line {ast['line']})"
        
        # Truncate text if too long
        text = ast.get('text', '')
        if len(text) > 50:
            text = text[:47] + "..."
        if text and text != ast['type']:
            node_info += f": '{text}'"
        
        lines.append(node_info)
        
        # Format children
        if 'children' in ast:
            for child in ast['children']:
                lines.append(QasmParser.format_ast(child, indent + 1))
        
        return '\n'.join(lines)


if PARSERS_AVAILABLE:
    from antlr4.error.ErrorListener import ErrorListener as BaseErrorListener
    
    class ErrorListener(BaseErrorListener):
        """Custom error listener for collecting parse errors"""
        
        def __init__(self):
            super().__init__()
            self.errors = []
        
        def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
            self.errors.append(f"Line {line}:{column} - {msg}")
else:
    class ErrorListener:
        """Dummy error listener when parsers not available"""
        def __init__(self):
            self.errors = []
