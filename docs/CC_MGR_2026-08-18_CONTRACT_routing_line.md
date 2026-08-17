# 契約: 振り分け1行の 書式(★2DER が 生成 ／ MGR は 置いただけ)

- 台帳: ITEM-2DER-EVO-0070 ／ task: TASK-2DER-5B669EFC

<<<2DER:SKELETON>>>
def make_routing_string(a, b, c, d):
    """Implement a function `make_routing_string(item: str, role: str, word: str, source: str) -> str` that returns a routing string. The format is 'ROUTING {item} | role={role} | word={word} | source={source}'. If `word` is empty, the output segment is 'word=' (i.e., no value after the equals sign). If `source` is empty, the function must return an empty string ''. The function must be pure, deterministic, and use only the Python standard library.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
<<<2DER:IMMUTABLE_TESTS>>>
from impl import make_routing_string

def test_normal_case():
    result = make_routing_string('item1', 'role1', 'word1', 'source1')
    assert result == 'ROUTING item1 | role=role1 | word=word1 | source=source1'

def test_empty_word():
    result = make_routing_string('item1', 'role1', '', 'source1')
    assert result == 'ROUTING item1 | role=role1 | word= | source=source1'

def test_empty_source():
    result = make_routing_string('item1', 'role1', 'word1', '')
    assert result == ''

def test_all_empty():
    result = make_routing_string('', '', '', '')
    assert result == ''

def test_special_chars():
    result = make_routing_string('it|em', 'ro|le', 'wo|rd', 'so|urce')
    assert result == 'ROUTING it|em | role=ro|le | word=wo|rd | source=so|urce'

def test_whitespace():
    result = make_routing_string(' ', ' ', ' ', ' ')
    assert result == 'ROUTING   | role=  | word=  | source= '

def test_none_values():
    try:
        make_routing_string(None, None, None, None)
        assert False, 'Should raise error for None'
    except (TypeError, AttributeError):
        pass
<<<2DER:END>>>
