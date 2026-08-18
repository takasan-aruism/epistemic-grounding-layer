BUILD_CAPABILITY: CC_MGR_2026-08-18_CONTRACT_extract_sealed_test_names.md

<<<2DER:SKELETON>>>
def extract_sealed_test_names(a):
    """Implement a pure function extract_sealed_test_names(text) that takes a single string argument representing a document body. The function must validate that the input is a string, raising TypeError otherwise. It should identify a section delimited by a start marker line '<2DER:IMMUTABLE_TESTS>' and an end marker line '<2DER:END>', where marker lines are matched exactly after stripping surrounding whitespace. If markers are missing, multiple start markers exist, or the end marker is absent, appropriate defaults (empty list or first marker usage) apply. Within the section, extract function names from lines that start with 'def ', have no leading whitespace, and define functions whose names start with 'test'. Names are extracted from 'def ' to the first '(', must be unique, case-sensitive, and returned in order of appearance. Return an empty list if no valid tests are found or input is empty.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

<<<2DER:IMMUTABLE_TESTS>>>
from impl import extract_sealed_test_names

def test_empty_string():
    assert extract_sealed_test_names("") == []

def test_no_markers():
    assert extract_sealed_test_names("def test_foo(): pass") == []

def test_markers_no_tests():
    text = "<2DER:IMMUTABLE_TESTS>\n<2DER:END>"
    assert extract_sealed_test_names(text) == []

def test_valid_test():
    text = "<2DER:IMMUTABLE_TESTS>\ndef test_foo(): pass\n<2DER:END>"
    assert extract_sealed_test_names(text) == ["test_foo"]

def test_leading_whitespace():
    text = "<2DER:IMMUTABLE_TESTS>\n    def test_bar(): pass\n<2DER:END>"
    assert extract_sealed_test_names(text) == []

def test_duplicate():
    text = "<2DER:IMMUTABLE_TESTS>\ndef test_foo(): pass\ndef test_foo(): pass\n<2DER:END>"
    assert extract_sealed_test_names(text) == ["test_foo"]

def test_case_sensitive():
    text = "<2DER:IMMUTABLE_TESTS>\ndef Test_foo(): pass\ndef test_bar(): pass\n<2DER:END>"
    assert extract_sealed_test_names(text) == ["test_bar"]

def test_non_string():
    try:
        extract_sealed_test_names(123)
        assert False
    except TypeError:
        pass

def test_multiple_start_markers():
    text = "<2DER:IMMUTABLE_TESTS>\ndef test_a(): pass\n<2DER:IMMUTABLE_TESTS>\ndef test_b(): pass\n<2DER:END>"
    assert extract_sealed_test_names(text) == ["test_a"]

def test_end_before_start():
    text = "<2DER:END>\ndef test_foo(): pass\n<2DER:IMMUTABLE_TESTS>"
    assert extract_sealed_test_names(text) == []

def test_name_extraction():
    text = "<2DER:IMMUTABLE_TESTS>\ndef test_func(arg): pass\n<2DER:END>"
    assert extract_sealed_test_names(text) == ["test_func"]

def test_no_leading_space_in_def():
    text = "<2DER:IMMUTABLE_TESTS>\n  def test_foo(): pass\n<2DER:END>"
    assert extract_sealed_test_names(text) == []

<<<2DER:END>>>
