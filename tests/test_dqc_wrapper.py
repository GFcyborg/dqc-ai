"""
Test DQC pragma parser wrapper
"""
import sys
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]

# Add src/main/python to path
sys.path.insert(0, str(PROJECT_DIR / 'src' / 'main' / 'python'))

from parser.dqc_parser import DQCPragmaParser, DQCPragma, DQC_PARSERS_AVAILABLE


def test_dqc_wrapper():
    """Test the DQC pragma parser wrapper"""

    if not DQC_PARSERS_AVAILABLE:
        print("Skipping DQC wrapper test: generated parsers not available.")
        print("Run ./gradlew generateDQCGrammar to enable this test.")
        return True
    
    # Sample .dqc file content with flexible whitespace
    test_content = """OPENQASM 3.0;
include "stdgates.inc";

// Chunk 0 (implicit initial chunk)
qubit[2] q;
bit[2] c;

pragma dqc . v1 . split  id = 1
// Chunk 1 starts here
h q[0];
cx q[0], q[1];

pragma  dqc.v1.split id= 2
// Chunk 2 starts here
measure q -> c;
"""
    
    print("Testing DQC Pragma Parser Wrapper")
    print("="*60)
    print("\nTest content (with flexible whitespace):")
    print(test_content)
    print("\n" + "="*60 + "\n")
    
    # Create parser
    parser = DQCPragmaParser()
    
    # Parse content
    pragmas = parser.parse_string(test_content)
    
    print(f"Found {len(pragmas)} pragma(s):\n")
    
    for pragma in pragmas:
        print(f"  Line {pragma.line_number}: {pragma.raw_text}")
        print(f"    - Version: {pragma.version}")
        print(f"    - Split ID: {pragma.split_id}")
        print()
    
    # Validate sequence
    is_valid, error = DQCPragmaParser.validate_pragma_sequence(pragmas)
    
    if is_valid:
        print("✓ Pragma sequence is valid!")
        print(f"  Total chunks: {len(pragmas) + 1} (chunk 0 is implicit)")
    else:
        print(f"✗ Pragma sequence validation failed: {error}")
        return False
    
    print("\n" + "="*60)
    print("\nTest additional edge cases:")
    
    # Test invalid sequence (missing ID)
    invalid_content = """pragma dqc.v1.split id=1
pragma dqc.v1.split id=3
"""
    pragmas_invalid = parser.parse_string(invalid_content)
    is_valid, error = DQCPragmaParser.validate_pragma_sequence(pragmas_invalid)
    
    if not is_valid:
        print(f"✓ Correctly detected invalid sequence: {error}")
    else:
        print("✗ Failed to detect invalid sequence")
        return False
    
    # Test starting from wrong ID
    invalid_start = """pragma dqc.v1.split id=2"""
    pragmas_bad_start = parser.parse_string(invalid_start)
    is_valid, error = DQCPragmaParser.validate_pragma_sequence(pragmas_bad_start)
    
    if not is_valid:
        print(f"✓ Correctly detected bad start: {error}")
    else:
        print("✗ Failed to detect bad start")
        return False
    
    # Test split_id = 0 (should be rejected by regex pattern, not matched)
    print("\n" + "="*60)
    print("\nTest chunk ID validation (must be >= 1):")
    
    invalid_zero = """pragma dqc.v1.split id=0"""
    pragmas_zero = parser.parse_string(invalid_zero)
    if len(pragmas_zero) == 0:
        print("✓ Correctly ignored split_id=0 (not matched by pattern [1-9][0-9]*)")
    else:
        print(f"✗ Unexpectedly parsed split_id=0: {pragmas_zero}")
        return False
    
    # Test negative split_id (should not match pattern)
    invalid_negative = """pragma dqc.v1.split id=-1"""
    pragmas_neg = parser.parse_string(invalid_negative)
    if len(pragmas_neg) == 0:
        print("✓ Correctly ignored negative split_id (not matched by pattern)")
    else:
        print("✗ Unexpectedly parsed negative split_id")
        return False
    
    print("\n" + "="*60)
    print("\n✓ All tests passed!")
    return True


if __name__ == '__main__':
    try:
        success = test_dqc_wrapper()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
