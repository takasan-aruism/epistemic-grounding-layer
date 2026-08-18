BUILD_CAPABILITY: CC_MGR_2026-08-18_CONTRACT_tests_from_document.md

<<<2DER:SKELETON>>>
def extract_test_names(a):
    """Create a function `extract_test_names(doc: str) -> list[str]` in `impl.py`. The function extracts test names from `doc`. Logic: 1. Validate input is string, else TypeError. 2. If empty, return []. 3. Find first line with 'IMMUTABLE_TESTS' (start_idx). If not found, return []. 4. Find first line with 'END' after start_idx (end_idx). If not found, return []. 5. Iterate lines from start_idx+1 to end_idx. 6. For each line: if line.startswith('def'): extract name between 'def ' and first '('. 7. Check name.startswith('test') and not name.startswith('Test'). 8. Add to result if not seen. 9. Return result list.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

<<<2DER:IMMUTABLE_TESTS>>>
from impl import extract_test_names

def test_empty_input():
    assert extract_test_names('') == []

def test_non_string_input():
    try:
        extract_test_names(123)
        assert False, 'Should have raised TypeError'
    except TypeError:
        pass

def test_no_start_marker():
    doc = 'Some text\nEND\n'
    assert extract_test_names(doc) == []

def test_no_end_marker():
    doc = 'IMMUTABLE_TESTS\nsome text\n'
    assert extract_test_names(doc) == []

def test_valid_function():
    doc = 'IMMUTABLE_TESTS\ndef test_foo():\nEND\n'
    assert extract_test_names(doc) == ['test_foo']

def test_leading_whitespace():
    doc = 'IMMUTABLE_TESTS\n    def test_bar():\nEND\n'
    assert extract_test_names(doc) == []

def test_uppercase_prefix():
    doc = 'IMMUTABLE_TESTS\ndef Test_bar():\nEND\n'
    assert extract_test_names(doc) == []

def test_duplicate_names():
    doc = 'IMMUTABLE_TESTS\ndef test_foo():\ndef test_foo():\nEND\n'
    assert extract_test_names(doc) == ['test_foo']

def test_multiple_valid():
    doc = 'IMMUTABLE_TESTS\ndef test_a():\ndef test_b():\nEND\n'
    assert extract_test_names(doc) == ['test_a', 'test_b']

def test_no_valid_functions():
    doc = 'IMMUTABLE_TESTS\ndef helper():\nEND\n'
    assert extract_test_names(doc) == []

<<<2DER:END>>>
