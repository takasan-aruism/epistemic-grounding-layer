BUILD_CAPABILITY: CC_MGR_2026-08-18_CONTRACT_acceptance_fields.md

<<<2DER:SKELETON>>>
def assemble_acceptance(a):
    """Implement a pure function named `assemble_acceptance` that takes a single argument: a list of strings representing test names. The function must validate that the input is a list, that all elements are strings, and that no element is an empty string. If the input is not a list, raise `TypeError`. If any element is not a string, raise `TypeError`. If any element is an empty string, raise `ValueError`. The function returns a dictionary with two keys: `completion` and `required_tests`. If the input list is empty, `completion` must be the string `NO_COMPLETION_IN_DOCUMENT` and `required_tests` must be an empty list. If the input list is not empty, `required_tests` must be a new list containing the same elements in the same order as the input (a copy), and `completion` must be the string `TESTS_ALL_PASS:` followed by the decimal integer count of the list elements. The function must not modify the input list. The implementation must use only the Python standard library.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

<<<2DER:IMMUTABLE_TESTS>>>
from impl import assemble_acceptance

def test_empty_list():
    result = assemble_acceptance([])
    assert result["completion"] == "NO_COMPLETION_IN_DOCUMENT"
    assert result["required_tests"] == []

def test_non_list_input():
    try:
        assemble_acceptance("not a list")
        assert False, "Should raise TypeError"
    except TypeError:
        pass

def test_non_string_element():
    try:
        assemble_acceptance([1, 2])
        assert False, "Should raise TypeError"
    except TypeError:
        pass

def test_empty_string_element():
    try:
        assemble_acceptance(["test", ""])
        assert False, "Should raise ValueError"
    except ValueError:
        pass

def test_valid_list():
    result = assemble_acceptance(["test1", "test2"])
    assert result["completion"] == "TESTS_ALL_PASS:2"
    assert result["required_tests"] == ["test1", "test2"]

def test_copy_behavior():
    input_list = ["a", "b"]
    result = assemble_acceptance(input_list)
    result["required_tests"].append("c")
    assert input_list == ["a", "b"]

def test_duplicates():
    result = assemble_acceptance(["a", "a"])
    assert result["required_tests"] == ["a", "a"]
    assert result["completion"] == "TESTS_ALL_PASS:2"

def test_order_preservation():
    input_list = ["c", "a", "b"]
    result = assemble_acceptance(input_list)
    assert result["required_tests"] == ["c", "a", "b"]

def test_single_element():
    result = assemble_acceptance(["single"])
    assert result["completion"] == "TESTS_ALL_PASS:1"
    assert result["required_tests"] == ["single"]

def test_type_error_for_tuple():
    try:
        assemble_acceptance(("a", "b"))
        assert False, "Should raise TypeError"
    except TypeError:
        pass
<<<2DER:END>>>
