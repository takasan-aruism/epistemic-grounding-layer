# 【BUILD SPEC v2】`EVO-0055` — **★実体を返す口（★保存しない・★聞かれたら現物を見る）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-05 12:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.14）** ／ 親: `ITEM-2DER-EVO-0035` ／ 台帳: `ITEM-2DER-EVO-0055`（段5）
- **★着手は ★段4 完了後**（★裁定 維持）。★本書は ★設計を先に出すもの
- **★v1 からの差は ★試験を1本 足しただけ**（★既存は ★1本も緩めない・★依頼文は ★1文字も変えない）
- **★足した理由**: ★成果物が ★fixture の ★見出し文字列を ★直接 見ていた（MGR 実測）。★規則は ★`"%s"` が2つ、であって ★見出しではない
- **★v1.8 の宣言**: **★核は在る・1件**（`rebuild_requirement`＝純関数）→ **★2DER 工程 1 になりうる**
- **★私の予告**: ★worker の行数は書かない ／ ★Claude の配線 **8〜14行**（★走査と ★1欄）
- **★新台帳0・★新計器0・★保存0**（★記録を1バイトも増やさない）

---

## 1. ★答える問いは2つだけ

```
★(i) ★『★送った文』 = ★保存されていない ―― ★★決定論で ★組み直して返す
★(ii)★『★残った物』 = ★成果物が ★repo に在るか ―― ★★聞かれた時に ★機械がファイルを見る
★★共通の規律 = ★★人が『置いた』『送った』と書いた値を ★証拠にしない（v0.3 §13.3）
★★★保存しない ＝ ★`runtime_supervisor.py:194-196` の方針（★`no prompt/response text`）を ★反転させない
```

## 2. ★(ii) の探し方（★自己申告にしない・★今日の実害を機械化）

```
★配置先の path は ★2DER が ★知らない（★決めるのは Claude）∴ ★★path を ★人に申告させない。
★★代わりに ★★契約の骨格から ★関数名を ★決定論で取る（`def locate_failure(route, events):` → `locate_failure`）
★★★その名前の ★`def <name>` を含む `.py` が ★repo に在るかを ★走査する
★★★★これは ★2026-08-05 に ★監視インスタンスが ★手で grep したことと ★同じ操作である ＝ ★機械に移すだけ
```

## 3. ★★契約（★核・★そのまま封入できる形）

**★依頼文**
```
送った文を組み直す純関数 impl.rebuild_requirement を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
template = str   ★"%s" を2つ含むテンプレ。1つ目に skeleton、2つ目に tests が入る
skeleton = str
tests    = str
expected_sha256 = str|None   ★記録に残っている値。無ければ None
戻り値 = {"text": str, "sha256": str, "length": int, "match": bool|None}

・text = template に skeleton と tests を この順で埋めた文字列。
  ★template に "%s" が 2つ 無ければ ValueError を送出する。
・sha256 = text を utf-8 で符号化した SHA-256 の16進小文字。
・length = len(text)。
・match = expected_sha256 が None なら None。
  そうでなければ sha256 と expected_sha256 が 等しいかどうか。
  ★大文字小文字は無視して比べる。★先頭が一致するだけでは True にしない（★全体が等しいこと）。
・★expected_sha256 が 短くても 補わない・切らない（★等しくなければ False）。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def rebuild_requirement(template, skeleton, tests, expected_sha256=None):
    # <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

**★封印試験（★10本・★fixture は 2026-08-05 の実測）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import hashlib
import impl

TMPL = "head\n### skeleton:\n%s\n### immutable_tests:\n%s"
SK = "def locate_failure(route, events):"
TS = "import impl\n\ndef test_x():\n    assert True\n"

def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def test_text_puts_skeleton_then_tests():
    v = impl.rebuild_requirement(TMPL, SK, TS)
    assert v["text"] == TMPL % (SK, TS), v["text"]

def test_sha256_is_of_the_rebuilt_text():
    v = impl.rebuild_requirement(TMPL, SK, TS)
    assert v["sha256"] == _sha(TMPL % (SK, TS))

def test_length_is_the_character_count():
    v = impl.rebuild_requirement(TMPL, SK, TS)
    assert v["length"] == len(TMPL % (SK, TS))

def test_match_is_none_when_nothing_to_compare():
    assert impl.rebuild_requirement(TMPL, SK, TS)["match"] is None

def test_match_true_on_the_same_bytes():
    v = impl.rebuild_requirement(TMPL, SK, TS, _sha(TMPL % (SK, TS)))
    assert v["match"] is True

def test_match_false_when_one_character_differs():
    """★1文字 違えば False（★本日 1678字の別文を 同じだと読んだ形を 二度と作らない）"""
    v = impl.rebuild_requirement(TMPL, SK + " ", TS, _sha(TMPL % (SK, TS)))
    assert v["match"] is False

def test_match_ignores_letter_case():
    v = impl.rebuild_requirement(TMPL, SK, TS, _sha(TMPL % (SK, TS)).upper())
    assert v["match"] is True

def test_a_prefix_is_not_a_match():
    """★先頭16字だけの記録と 突き合わせても True にしない"""
    v = impl.rebuild_requirement(TMPL, SK, TS, _sha(TMPL % (SK, TS))[:16])
    assert v["match"] is False

def test_any_template_with_two_slots_works():
    """★見出しの文字列に ★依存しない ―― ★"%s" が2つ在れば ★どんなテンプレでも組める"""
    other = "A=%s|B=%s"
    v = impl.rebuild_requirement(other, SK, TS)
    assert v["text"] == other % (SK, TS), v["text"]

def test_template_without_two_slots_raises():
    try:
        impl.rebuild_requirement("no slots here", SK, TS)
    except ValueError:
        return
    raise AssertionError("ValueError が送出されなかった")
<<<2DER:END>>>
```

## 4. ★Claude の配線（★8〜14行と予告）

```
★(a) ★`/api/resolve?id=TASK-…` の record に ★2欄 足す（★EVO-0052 / EVO-0059 と ★同じ形・★新しい口を作らない）
     ★`sent`     = ★`rebuild_requirement(現テンプレ, 契約の骨格, 契約の試験, 記録の handoff_sha256)` の戻り
     ★`artifact` = ★骨格から取った関数名で ★repo を走査した結果 {"name":…, "found": bool, "paths":[…]}
★(b) ★走査は ★`.py` のみ・★`def <name>` の行一致・★repo 5本の直下から（★深い探索をしない）
★★保存しない = ★どちらも ★呼ばれた時に ★その場で作る
```

## 5. ★★これで分からないこと（★先に言う）

```
★★テンプレの ★版が ★記録に無い ∴ ★★過去の走行は ★★現在のテンプレでしか ★組み直せない。
   ★テンプレが変わっていれば ★`match=False` になる ―― ★★これは ★『再構成できなかった』の印であって
   ★『別の文が送られた』の証明ではない。★★合わせに行かない・★偽の一致を作らない。
★★★worker の ★★応答（raw 出力）は ★再構成できない ∴ ★本書に ★入らない（★別の1件・★今は立てない）
★★★★`artifact` の走査は ★★『同じ名前の別物』を ★区別しない（★名前一致だけ）
```

## 6. 受入

```
★(0) ★worker が `rebuild_requirement` を書く（★Claude は本文0行）・★10本 全通
★(1) ★★成功した走行1本で ★`sent.match` が ★★True（★記録の `handoff_sha256` と ★一致）
     ★★★一致しなければ ★★『一致しなかった』と ★sha を ★両方 書いて ★止まる（★§5）
★(2) ★`sent.length` を ★逐語で書く（★段3 v5 なら ★7520 前後の見込み）
★(3) ★★`artifact.found` が ★`locate_failure` で ★★False と出る（★2026-08-05 実測＝★repo に0件）
     ★★★`gate_decision` / `effective_state` / `route_table` では ★True と出る（★陽性対照）
★(4) ★保存が ★0（★新しいファイル・台帳・欄を ★作っていないことを ★示す）
★(5) ★自己申告の値を ★1つも使っていない（★人が書いた path も『置いた』の宣言も ★読まない）
★(6) ★Claude の行数 ／★(7) ★戻せる ／★(8) ★61本を走らせない ／★(9) ★commit しない
★★★★★予告を投入前に書く: ★行数 ／ ★(2) の length ／ ★(3) の 陽性・陰性の別
```

## 7. 禁止

```
★prompt / 応答 / 成果物の ★本文を ★保存する（★方針を反転させない）
★path を ★人に申告させる ／ ★『置いた』の宣言を ★証拠にする
★`match` を ★先頭一致で True にする ／ ★テンプレを ★合わせに行く（★§5）
★`.py` 以外を走査する ／ ★深い再帰で ★repo 全体を舐める（★上限を外さない）
★新しい台帳・エンドポイントを作る（★既存 `/api/resolve` の record に足す）
★★『何をしたか 全部 見えるようになった』と書く（★応答は入っていない）
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
