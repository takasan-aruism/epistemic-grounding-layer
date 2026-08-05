# 【BUILD SPEC】`EVO-0049` — **★『人が置く入力』を規則が認める（★1条件だけ）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-05 18:4x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.14）** ／ 親: `ITEM-2DER-EVO-0035` ／ 台帳: `ITEM-2DER-EVO-0049`
- **★v1.8 の宣言**: **★核は在る・1件**（`should_flag_no_writer`＝純関数）→ **★2DER 工程 1 になりうる**
- **★私の予告**: ★worker の行数は書かない ／ ★Claude の配線 **2〜4行**（★既存の1条件を ★述語に置き換える）
- **★新しい語0**（★`governance.git_tracked` は ★`s10_ledger_registry.py:289` に ★既に在る）
- **★新台帳0・★新エンドポイント0・★走行 0（★私は）**

---

## 1. ★いま鳴っている規則（★逐語）

```
★`egl/structure/s10_ledger_registry.py:319-320`:
    if r["live_referenced"] and r["writer_resolution"] == "NONE_ORPHAN":
        bad.append((r["ledger_id"], "live-read-but-genuinely-no-writer", []))
★★この規則は ★『読まれるのに 誰も書かない』を ★供給不能として鳴らす。
★★★しかし ★★『人が置いて 機械が読むだけ』の入力は ★書き手が居ないのが ★正常である
   （★実測: `rri/rri/ambiguity_patterns.jsonl` は ★git 追跡下・★書き手0本・
     ★`preflight_gate.py:50` 逐語『★detect() never writes counters back』）
```

## 2. ★★書き手0が正当になる条件（★条件(b)・★逐語で書く）

```
★★live で読まれ、★書き手が居ない台帳のうち:
   ★★`governance.git_tracked` が ★True → ★★『人が置く入力』とみなし ★鳴らさない
   ★★`governance.git_tracked` が ★False → ★従来どおり ★鳴らす
★★★理由 = ★実行時に生成される物(★git に入らない)に ★書き手が居ないのは ★供給不能。
   ★一方 ★git に入っている物は ★★人がコミットした ∴ ★書き手が居ないのが ★正常。
★★★★∴ ★『人が置く』を ★機械が判定する形が ★1つ増える(★語は増やさない)
```

## 3. ★★契約（★小さい）

**★依頼文**
```
台帳の警報を出すかどうかを決める純関数 impl.should_flag_no_writer を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
row = {"live_referenced": bool, "writer_resolution": str,
       "governance": {"git_tracked": bool}}
戻り値 = bool（True = 警報を出す / False = 出さない）

・live_referenced が True でなければ False。
・writer_resolution が "NONE_ORPHAN" でなければ False。
・ここまで来たら、governance の "git_tracked" を見る:
    True  → False（人が置く入力とみなす）
    それ以外（False / キーが無い / governance が dict でない） → True。
・★情報が足りない時は True を返す（★警報を消さない）。
・row が dict でなければ True。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def should_flag_no_writer(row):
    # <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

**★封印試験（★7本・★fixture は 2026-08-05 の実測から）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

# 実測: rri/rri/ambiguity_patterns.jsonl = live 参照あり / 書き手0 / git 追跡下
AUTHORED = {"live_referenced": True, "writer_resolution": "NONE_ORPHAN",
            "governance": {"git_tracked": True}}
RUNTIME = {"live_referenced": True, "writer_resolution": "NONE_ORPHAN",
           "governance": {"git_tracked": False}}

def test_authored_input_is_not_flagged():
    """★人が置く入力(★git 追跡下・書き手0)は ★鳴らさない"""
    assert impl.should_flag_no_writer(AUTHORED) is False

def test_runtime_data_without_writer_is_still_flagged():
    """★実行時に作られる物に 書き手が居ないのは ★従来どおり 鳴らす"""
    assert impl.should_flag_no_writer(RUNTIME) is True

def test_not_live_is_never_flagged():
    assert impl.should_flag_no_writer(dict(RUNTIME, live_referenced=False)) is False

def test_having_a_writer_is_never_flagged():
    assert impl.should_flag_no_writer(dict(RUNTIME, writer_resolution="SINGLE")) is False

def test_missing_git_tracked_key_still_flags():
    """★情報が足りない時は ★警報を消さない"""
    assert impl.should_flag_no_writer({"live_referenced": True,
                                       "writer_resolution": "NONE_ORPHAN",
                                       "governance": {}}) is True

def test_governance_not_a_dict_still_flags():
    assert impl.should_flag_no_writer({"live_referenced": True,
                                       "writer_resolution": "NONE_ORPHAN",
                                       "governance": None}) is True

def test_non_dict_row_still_flags():
    assert impl.should_flag_no_writer(None) is True
<<<2DER:END>>>
```

## 4. ★Claude の配線（★2〜4行）

```python
# s10_ledger_registry.py:319-320 の条件を 述語に置き換える
            from twoder.should_flag_no_writer import should_flag_no_writer as _flag
            if _flag(r):
                bad.append((r["ledger_id"], "live-read-but-genuinely-no-writer", []))
```
```
★他の検査(declared-sole / CANONICAL 系)は ★1文字も触らない
★★語も ★増やさない（★`live-read-but-genuinely-no-writer` の文言は ★そのまま）
```

## 5. 受入

```
★(0) ★worker が書く（★Claude は本文0行）・★7本 全通
★(1) ★★`--check` を ★★変更前と変更後で ★1回ずつ 走らせ、★★出力を ★両方 逐語で残す
★(2) ★★差が ★★`rri/rri/ambiguity_patterns.jsonl` の ★1件だけであること
     ★★★他の55台帳の判定が ★1件も変わっていないことを ★逐語で示す（★条件(c)）
     ★★★★1件でも他が変われば ★★止まる（★合わせに行かない）
★(3) ★`--check` が ★GREEN になる（★mismatch 0）
★(4) ★`--apply` は ★走らせない（★登記簿は ★書き換えない）
★(5) ★sha256 一致 ／★(6) ★Claude の配線行数 ／★(7) ★戻せる ／★(8) ★61本を走らせない ／★(9) ★commit しない
★★★★★予告を投入前に書く: ★行数 ／ ★(2) で ★他が変わると思うか（★私の見込みは ★変わらない）
```

## 6. ★★これで直らないこと（★先に言う・★別の1件）

```
★★この表の ★自動抑制は ★動かないままである = ★`preflight_gate.py:78-81` の `is_suppressed` は
   ★`ignored_warning_count >= 3` で抑制するが、★★そのカウンタを ★増やす書き手が ★0本
   ∴ ★★値は ★永久に 0 ＝ ★自動抑制は ★一度も発火しない。
★★★本件は ★★『登記の判定』を直すだけで、★★『機能が動かない』方は ★直さない（★別の1件・★名指しで残す）
★★★★手で立てる `suppressed` は ★効く（★人が書けるため）∴ ★手動の抑制は ★生きている
```

## 7. 禁止

```
★`--apply` を走らせる ／ ★登記簿(LEDGER_REGISTRY.jsonl)を ★書き換える
★他の検査(declared-sole / CANONICAL)を ★触る ／ ★新しい語・欄を作る
★`git_tracked` が ★無い時に ★False を返す（★警報を消さない）
★自動抑制を ★本件で直す（★§6・別の1件）
★★他の55台帳の判定が変わった時に ★『些細だから』と ★進める（★止まる）
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
