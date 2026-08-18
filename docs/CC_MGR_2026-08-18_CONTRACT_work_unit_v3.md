BUILD_CAPABILITY: CC_MGR_2026-08-18_CONTRACT_work_unit_v3.md

<<<2DER:SKELETON>>>
def assemble_work_unit_v2(a, b, c, d):
    """Create a pure function assemble_work_unit_v2(serial_number: int, type_code: str, source: str, acceptance: dict) -> dict. The function must validate inputs strictly: serial_number must be an int (not bool), type_code must be a 2-char uppercase letter string, source must be a non-empty string, acceptance must be a dict with keys 'completion' and 'required_tests', completion must be a non-empty string, and required_tests must be a list of strings. Raise ValueError for value violations (negative serial, invalid type_code format, empty source, missing keys, empty completion). Raise TypeError for type violations (wrong types for any arg, bool for serial, non-list required_tests, non-string elements). On success, return a dict with keys: work_unit_id (format 'WU-{type_code}-{serial_number:04d}'), type (type_code), source (source), dependency ([]), completion (acceptance['completion']), required_tests (new list copy of acceptance['required_tests']). Ensure no mutation of inputs. Use only standard library.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

<<<2DER:IMMUTABLE_TESTS>>>
from impl import assemble_work_unit_v2

def test_valid_input():
    result = assemble_work_unit_v2(1, 'AB', 'Source1', {'completion': 'done', 'required_tests': ['t1', 't2']})
    assert result['work_unit_id'] == 'WU-AB-0001'
    assert result['type'] == 'AB'
    assert result['source'] == 'Source1'
    assert result['dependency'] == []
    assert result['completion'] == 'done'
    assert result['required_tests'] == ['t1', 't2']
    # Check no mutation
    assert result['required_tests'] is not ['t1', 't2']

def test_valid_input_zero_serial():
    result = assemble_work_unit_v2(0, 'XY', 'Src', {'completion': 'ok', 'required_tests': []})
    assert result['work_unit_id'] == 'WU-XY-0000'
    assert result['required_tests'] == []

def test_value_error_negative_serial():
    try:
        assemble_work_unit_v2(-1, 'AB', 'Src', {'completion': 'ok', 'required_tests': []})
        assert False, 'Expected ValueError'
    except ValueError:
        pass

def test_value_error_invalid_type_code():
    try:
        assemble_work_unit_v2(1, 'a', 'Src', {'completion': 'ok', 'required_tests': []})
        assert False, 'Expected ValueError'
    except ValueError:
        pass
    try:
        assemble_work_unit_v2(1, 'ABC', 'Src', {'completion': 'ok', 'required_tests': []})
        assert False, 'Expected ValueError'
    except ValueError:
        pass
    try:
        assemble_work_unit_v2(1, '12', 'Src', {'completion': 'ok', 'required_tests': []})
        assert False, 'Expected ValueError'
    except ValueError:
        pass

def test_value_error_empty_source():
    try:
        assemble_work_unit_v2(1, 'AB', '', {'completion': 'ok', 'required_tests': []})
        assert False, 'Expected ValueError'
    except ValueError:
        pass

def test_value_error_missing_completion_key():
    try:
        assemble_work_unit_v2(1, 'AB', 'Src', {'required_tests': []})
        assert False, 'Expected ValueError'
    except ValueError:
        pass

def test_value_error_missing_required_tests_key():
    try:
        assemble_work_unit_v2(1, 'AB', 'Src', {'completion': 'ok'})
        assert False, 'Expected ValueError'
    except ValueError:
        pass

def test_value_error_empty_completion():
    try:
        assemble_work_unit_v2(1, 'AB', 'Src', {'completion': '', 'required_tests': []})
        assert False, 'Expected ValueError'
    except ValueError:
        pass

def test_type_error_serial_not_int():
    try:
        assemble_work_unit_v2(1.0, 'AB', 'Src', {'completion': 'ok', 'required_tests': []})
        assert False, 'Expected TypeError'
    except TypeError:
        pass

def test_type_error_serial_bool():
    try:
        assemble_work_unit_v2(True, 'AB', 'Src', {'completion': 'ok', 'required_tests': []})
        assert False, 'Expected TypeError'
    except TypeError:
        pass

def test_type_error_type_code_not_str():
    try:
        assemble_work_unit_v2(1, 123, 'Src', {'completion': 'ok', 'required_tests': []})
        assert False, 'Expected TypeError'
    except TypeError:
        pass

def test_type_error_source_not_str():
    try:
        assemble_work_unit_v2(1, 'AB', 123, {'completion': 'ok', 'required_tests': []})
        assert False, 'Expected TypeError'
    except TypeError:
        pass

def test_type_error_acceptance_not_dict():
    try:
        assemble_work_unit_v2(1, 'AB', 'Src', 'not_dict')
        assert False, 'Expected TypeError'
    except TypeError:
        pass

def test_type_error_completion_not_str():
    try:
        assemble_work_unit_v2(1, 'AB', 'Src', {'completion': 123, 'required_tests': []})
        assert False, 'Expected TypeError'
    except TypeError:
        pass

def test_type_error_required_tests_not_list():
    try:
        assemble_work_unit_v2(1, 'AB', 'Src', {'completion': 'ok', 'required_tests': 'not_list'})
        assert False, 'Expected TypeError'
    except TypeError:
        pass

def test_type_error_required_tests_elements_not_str():
    try:
        assemble_work_unit_v2(1, 'AB', 'Src', {'completion': 'ok', 'required_tests': [123]})
        assert False, 'Expected TypeError'
    except TypeError:
        pass

def test_no_mutation():
    acc = {'completion': 'ok', 'required_tests': ['t1']}
    result = assemble_work_unit_v2(1, 'AB', 'Src', acc)
    assert acc['required_tests'] == ['t1']
    assert result['required_tests'] is not acc['required_tests']

def test_idempotency():
    r1 = assemble_work_unit_v2(1, 'AB', 'Src', {'completion': 'ok', 'required_tests': ['t1']})
    r2 = assemble_work_unit_v2(1, 'AB', 'Src', {'completion': 'ok', 'required_tests': ['t1']})
    assert r1 == r2

<<<2DER:END>>>
