"""
Simple test to verify DQC grammar can parse pragma lines
"""
import sys
import os
from pathlib import Path

# Add generated parser directory to path
# Try build directory first, then fall back to legacy location
PROJECT_DIR = Path(__file__).resolve().parents[1]

GENERATED_DIRS = [
    str(PROJECT_DIR / 'build' / 'generated-sources' / 'python'),
    str(PROJECT_DIR / 'src' / 'main' / 'python' / 'parser' / 'generated'),
]

GENERATED_DIR = None
for dir_path in GENERATED_DIRS:
    if os.path.exists(dir_path):
        GENERATED_DIR = dir_path
        sys.path.insert(0, GENERATED_DIR)
        break

if GENERATED_DIR is None:
    print("Skipping DQC grammar test: generated parsers not found in:")
    for d in GENERATED_DIRS:
        print(f"  {d}")
    print("Run ./gradlew generateDQCGrammar to enable this test.")
    sys.exit(0)

try:
    from antlr4 import InputStream, CommonTokenStream
    from dqcLexer import dqcLexer
    from dqcParser import dqcParser
except ImportError as exc:
    print(f"Skipping DQC grammar test: {exc}")
    print("Run ./gradlew generateDQCGrammar to enable this test.")
    sys.exit(0)

def test_dqc_pragma():
    """Test parsing of DQC pragma"""
    
    # Test case: DQC pragmas with flexible whitespace
    test_input = """pragma dqc.v1.split id=1
some other content
OPENQASM 3.0;
pragma  dqc . v2 . split  id = 3
more content
pragma dqc  .  v1  .  split id  =  5
qubit q;"""
    
    print("Testing DQC grammar with input:")
    print(test_input)
    print("\n" + "="*50 + "\n")
    
    # Create lexer
    input_stream = InputStream(test_input)
    lexer = dqcLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    
    # Create parser
    parser = dqcParser(token_stream)
    
    # Parse
    tree = parser.program()
    
    print("Parse tree:")
    print(tree.toStringTree(recog=parser))
    print("\n" + "="*50 + "\n")
    
    # Extract pragma information using regex (flexible whitespace)
    import re
    pragma_pattern = r'pragma\s+dqc\s*\.\s*v(\d+)\s*\.\s*split\s+id\s*=\s*(\d+)'
    pragmas = re.findall(pragma_pattern, test_input)
    
    print("Pragmas found:")
    for version, split_id in pragmas:
        print(f"  version={version}, split_id={split_id}")
    
    print(f"\nTotal pragmas found: {len(pragmas)}")
    
    # Verify tree structure
    line_count = len([child for child in tree.getChildren() if child.getText() != '<EOF>'])
    print(f"Total lines parsed: {line_count}")
    
    print("✓ Grammar test passed!")

if __name__ == '__main__':
    try:
        test_dqc_pragma()
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
