# 契約: determine_role(★2DER が 生成 ／ MGR は 置いただけ)

- 台帳: ITEM-2DER-EVO-0070 ／ task: TASK-2DER-9764F362
- 骨格と 封印試験は ★`contract_from_plan`(2DER)が 生成。★MGR は 1文字も 書いていない。

<<<2DER:SKELETON>>>
def determine_role(a):
    """Create a function `determine_role` in `impl.py` that accepts a single string argument. The function must check for the presence of specific Japanese keywords: '経路', '環境', '契約', '失敗', '外部'. Map these to roles: 'ROUTE', 'ENV', 'SUCCESS', 'FAILURE', 'EXTERNAL' respectively. If a keyword is found, return a tuple containing the matched keyword and its role. If no keyword is found, return a tuple containing the original input string and 'NO_ROLE_FOR_THIS_WORD'. The function must be pure, deterministic, and use only the Python standard library.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
<<<2DER:IMMUTABLE_TESTS>>>
from impl import determine_role

def test_keiro():
    assert determine_role('経路') == ('経路', 'ROUTE')

def test_kankyou():
    assert determine_role('環境') == ('環境', 'ENV')

def test_keiyaku():
    assert determine_role('契約') == ('契約', 'SUCCESS')

def test_shippai():
    assert determine_role('失敗') == ('失敗', 'FAILURE')

def test_gaibu():
    assert determine_role('外部') == ('外部', 'EXTERNAL')

def test_no_match():
    assert determine_role('未知語') == ('未知語', 'NO_ROLE_FOR_THIS_WORD')

def test_empty():
    assert determine_role('') == ('', 'NO_ROLE_FOR_THIS_WORD')

def test_substring():
    assert determine_role('経路探索') == ('経路', 'ROUTE')

def test_multiple_matches():
    assert determine_role('経路と環境') == ('経路', 'ROUTE')
<<<2DER:END>>>
