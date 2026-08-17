# 契約: 根拠が 成立するかの 判定(★2DER が 生成 ／ MGR は 置いただけ)

- 台帳: ITEM-2DER-EVO-0071 ／ task: TASK-2DER-3CBD0AB1 ／ ★目的=Manager の 判定を 部品へ 移す

<<<2DER:SKELETON>>>
def validate_material(a, b, c):
    """Create a pure Python function named validate_material in impl.py that takes three arguments: material (str), search_terms (list of str), and count (int or None). The function must return a tuple of (judgment: str, verified_count: int or None, hit_count: int). If material is an empty string, return ('NO_MATERIAL', count, 0). If count is None, return ('UNVERIFIED', None, 0). Otherwise, search for each term in search_terms within material; if at least one term is found, return ('ESTABLISHED', count, number_of_hits); if no terms are found, return ('CONDITION_NOT_MET', count, 0). The function must be deterministic and use only the Python standard library. Create test_impl.py to test all cases including empty material, None count, terms found, terms not found, empty search terms, and multiple hits.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
<<<2DER:IMMUTABLE_TESTS>>>
from impl import validate_material

def test_empty_material():
    result = validate_material('', ['term'], 10)
    assert result == ('NO_MATERIAL', 10, 0)

def test_none_count():
    result = validate_material('material', ['term'], None)
    assert result == ('UNVERIFIED', None, 0)

def test_term_found():
    result = validate_material('This is a material with term', ['term'], 10)
    assert result == ('ESTABLISHED', 10, 1)

def test_multiple_hits():
    result = validate_material('term term term', ['term'], 10)
    assert result == ('ESTABLISHED', 10, 3)

def test_no_term_found():
    result = validate_material('No match here', ['term'], 10)
    assert result == ('CONDITION_NOT_MET', 10, 0)

def test_empty_search_terms():
    result = validate_material('material', [], 10)
    assert result == ('CONDITION_NOT_MET', 10, 0)

def test_count_zero():
    result = validate_material('material', ['term'], 0)
    assert result == ('CONDITION_NOT_MET', 0, 0)

def test_special_characters():
    result = validate_material('term@#$%', ['term'], 10)
    assert result == ('ESTABLISHED', 10, 1)

def test_long_material():
    long_mat = 'term ' * 1000
    result = validate_material(long_mat, ['term'], 10)
    assert result == ('ESTABLISHED', 10, 1000)

def test_case_sensitivity():
    result = validate_material('Term', ['term'], 10)
    assert result == ('ESTABLISHED', 10, 1)

def test_multiple_terms():
    result = validate_material('term1 and term2', ['term1', 'term2'], 10)
    assert result == ('ESTABLISHED', 10, 2)

def test_no_match_multiple_terms():
    result = validate_material('no match', ['term1', 'term2'], 10)
    assert result == ('CONDITION_NOT_MET', 10, 0)

<<<2DER:END>>>
