# 【BUILD SPEC】`EVO-0035` — **★我々の失敗を 登録する口（★印に1欄・★引く核1つ）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-06 11:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.15）** ／ 親: `ITEM-2DER-EVO-0035`
- **★v1.8 の宣言**: **★核は在る・1件**（`recent_failure_for_stage`＝純関数）→ **★2DER 工程 1 になりうる**
- **★私の予告**: ★worker の行数は書かない ／ ★Claude の配線 **1〜3行**（★印の欄を1語）
- **★新台帳0・★新エンドポイント0・★新しい置き場0**

---

## 1. ★★MGR の §3 の形を ★採る（★理由を ★実測で 足す）

```
★★既存の `failure_memory.jsonl` には ★入れない。★理由は ★schema が ★合わないから（★実測）:
   ★その表の欄 = `failure_id` / `kind` / ★`match_keywords` / ★`raw_input_examples` /
                 `match_signal` / `regression_ref` / `wrong_interpretation` / `ref` / `status`
   ★★∴ ★これは ★★『投入文を見て 当てる』ための表である。
★★★我々の失敗（★例『規則を書いたが 試験で縛らなかった』）は ★★投入文で当てる物ではない。
   ★★引く鍵は ★★工程（`stage`）＝ ★設計(b) の裁定どおり。
★★★★∴ ★2つ在るのは ★重複ではなく ★★役割違いである。★同じ置き場に ★入れない方が 正しい。
★★★★★∴ ★MGR の案（★進捗の印に `failure:` を1欄）を ★採る。★置き場は ★既存の台帳の note。
```

## 2. 変更①（★`twoder/progress_seal.py` の ★1語）

```python
OPTIONAL = ("phase", "title", "note", "failure")     # ★1語 足すだけ
```
```
★`REQUIRED` は ★1文字も触らない（★item / actor / stage の3つのまま）
★★`failure` は ★任意 ∴ ★既存の投入は ★1つも壊れない
★★★書けるのは ★MGR・設計・IMPL・監視（★4者とも ★既に この印を使っている）
```

## 3. ★★契約（★引く核）

**★依頼文**
```
その工程で直前に起きた失敗を1件返す純関数 impl.recent_failure_for_stage を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
records = [ {"stage": str, "failure": str, "actor": str, "ts": str}, ... ]
stage   = str
戻り値 = {"failure": str|None, "actor": str|None, "ts": str|None}

・records が list でなければ すべて None。
・record が dict であり、"stage" が stage と 文字ごとに等しく、
  "failure" が 中身のある str（空白だけでない）である物だけを 対象にする。
・対象のうち "ts" が いちばん大きい物を 1件 返す。
  ts が 同じ物が 複数ある時は、records の 後ろにある物を 返す。
・"ts" が str でない record は 対象にしない。
・対象が 0件なら すべて None。
・★返すのは 1件だけ（設計(a) の裁定）。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def recent_failure_for_stage(records, stage):
    # <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

**★封印試験（★9本・★fixture は MGR §4 の実物）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

# MGR §4 の実物（★本日の 我々の非）
R = [{"stage": "PLAN", "failure": "規則を書いたが 試験で縛らなかった",
      "actor": "Claude", "ts": "2026-08-06T09:00:00"},
     {"stage": "VERIFY", "failure": "申告を 実測と 書いた",
      "actor": "MGR", "ts": "2026-08-06T10:00:00"},
     {"stage": "PLAN", "failure": "依頼文に書いて 試験で縛らなかった",
      "actor": "Claude", "ts": "2026-08-06T11:00:00"}]

def test_returns_the_latest_for_that_stage():
    """★同じ工程が 2件 在る時は ★ts が 大きい方を 返す"""
    v = impl.recent_failure_for_stage(R, "PLAN")
    assert v["failure"] == "依頼文に書いて 試験で縛らなかった", v

def test_returns_the_actor_and_ts_together():
    v = impl.recent_failure_for_stage(R, "PLAN")
    assert (v["actor"], v["ts"]) == ("Claude", "2026-08-06T11:00:00"), v

def test_other_stage_is_returned_for_that_stage():
    v = impl.recent_failure_for_stage(R, "VERIFY")
    assert v["failure"] == "申告を 実測と 書いた", v

def test_unknown_stage_gives_all_none():
    v = impl.recent_failure_for_stage(R, "EXECUTE")
    assert (v["failure"], v["actor"], v["ts"]) == (None, None, None), v

def test_stage_is_compared_exactly():
    """★大文字小文字を そろえない（★`plan` は `PLAN` と 別）"""
    assert impl.recent_failure_for_stage(R, "plan")["failure"] is None

def test_blank_failure_is_skipped():
    rs = [{"stage": "PLAN", "failure": "   ", "actor": "MGR", "ts": "2026-08-06T12:00:00"}] + R
    assert impl.recent_failure_for_stage(rs, "PLAN")["failure"] == "依頼文に書いて 試験で縛らなかった"

def test_record_without_string_ts_is_skipped():
    rs = R + [{"stage": "PLAN", "failure": "後から来た物", "actor": "MGR", "ts": 99}]
    assert impl.recent_failure_for_stage(rs, "PLAN")["failure"] == "依頼文に書いて 試験で縛らなかった"

def test_same_ts_takes_the_later_one():
    rs = [{"stage": "PLAN", "failure": "先", "actor": "MGR", "ts": "T"},
          {"stage": "PLAN", "failure": "後", "actor": "MGR", "ts": "T"}]
    assert impl.recent_failure_for_stage(rs, "PLAN")["failure"] == "後"

def test_non_list_gives_all_none():
    v = impl.recent_failure_for_stage(None, "PLAN")
    assert (v["failure"], v["actor"], v["ts"]) == (None, None, None), v
<<<2DER:END>>>
```

## 4. 受入

```
★(0) ★worker が書く（★Claude は本文0行）・★9本 全通
★(1) ★★`failure:` を1つ 含む投入を1本 行い、★`/api/resolve` の note に ★その語が ★逐語で 読める
★(2) ★`failure:` を ★含まない投入が ★従来どおり 通る（★既存を壊していない）
★(3) ★`REQUIRED` が ★item / actor / stage の3つのままであること
★(4) ★★MGR §4 の7件を ★登録し、★★`recent_failure_for_stage` に ★工程を渡して ★1件 返ること
★(5) ★sha256 一致 ／★(6) ★Claude の配線行数 ／★(7) ★戻せる ／★(8) ★61本を走らせない ／★(9) ★commit しない
★★★★★予告を投入前に書く: ★行数 ／ ★(4) で ★`PLAN` に対して 返ると思う1件
```

## 5. ★★本件に 入れないこと（★次の1件・★名指しで残す）

```
★★『状況表に 1行 出す』（★設計(c) の裁定）は ★★本件に 入れない。
   ★理由 = ★状況表を作っているのは ★`.claude/hooks/2der_status.sh` ＝ ★★2DER の外である。
   ★★∴ ★出す所を作るのは ★★管理層を中へ移す話（`EVO-0055`）と ★同じ構図であり、★同じ単位で扱う。
★★★本件で 出来るのは ★★『書ける』と『引ける』まで。★★『場面で 目に入る』は ★次。
★★★★∴ ★★『失敗が 場面で効くようになった』とは ★書かない。
```

## 6. 禁止

```
★`failure` を ★`REQUIRED` に入れる（★既存の投入が 全部 壊れる）
★既存の `failure_memory.jsonl` に ★我々の失敗を 入れる（★§1・★鍵が違う）
★新しい台帳・置き場・エンドポイントを作る ／ ★2件以上 返す（★設計(a)＝1件）
★`stage` を ★大文字小文字をそろえて 比べる（★別の工程が 混ざる）
★★『場面で効くようになった』と書く（★§5）
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
