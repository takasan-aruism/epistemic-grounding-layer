# AXIS: reader 検出器の品質評価 v0.1（修正前の実測）

**作成: Claude Code（MGR）／ 2026-08-23**
**指示: Taka 逐語「AXIS は reader 検出器の品質評価として扱う。偽陰性・偽陽性の両方を測ること。
先に『真の reader』の決定論的定義を置き、その定義を検出器自身の出力から作らないこと。
分母を固定し TP / FP / FN / TN を出す。… rthread_events.jsonl だけ通る修理は禁止。
全台帳で一般化していることを確認する」**

## 1. 対象（検出器）

`egl/structure/s10_ledger_registry.py:180-182`
```python
def readers(base, writers):
    rs = [k for k, txt in PY.items() if base in txt and k not in writers]
    return sorted(rs)
```
★**basename の部分文字列一致だけ**。読んでいるかは見ない。

## 2. 「真の reader」の決定論的定義（★検出器の出力を使わない）

**別の機構（`ast`）で作った。** 検出器は `base in txt` の部分文字列一致、こちらは import/呼び出しの構文解析。

```
Owner(L) = L の basename が ★Call の引数（os.path.join / open / Path）に現れる .py
           ★Set/List/Dict の要素として並んでいるだけの file は Owner にしない
読み関数  = Owner 内で _read / open / _EVENTS に到達する関数（★2段まで）
GT(L)    = { F : F が L を直接開く } ∪ { F : F が Owner を import し、読み関数を呼ぶ }
```

★**GT 自体を2回直した**（真値が壊れていたら測定にならないため）:
1. `CANONICAL_LEDGERS` のリテラル一覧に名前が在るだけの `s10` を Owner と誤判定 → Call 引数に限定
2. `from x import y as z` / `from rri import request_thread as RT` の**別名を元の名前へ戻していなかった**
   → `webui` / `submit` / `ids` / `manager_v0` / `account_candidates` を取りこぼしていた

**GT の限界（隠さない）**
- 動的 import（importlib）・getattr での呼び出しは拾えない
- 文字列を組み立てて path を作る場合、Owner を特定できないことがある
- 3段以上の間接呼び出し（A→B→C→`_read`）は 2段までしか辿らない

## 3. 分母と結果（★修正前）

```
分母 = 56台帳 × 767 .py = 42,952 判定

TP = 172   FP = 442   FN = 214   TN = 42,124
precision = 0.280      recall = 0.446
```

### 偽陽性の型（442件）
| 型 | 件数 | 中身 |
|---|---|---|
| **comment / docstring のみ** | **329** | 名前がコメント・文字列にしか現れない（本文から落とすと消える） |
| **basename 直書きだが読まない** | **80** | 名前は在るが open も読み関数呼びも無い |
| **registry 自身の自己参照** | **32** | `s10_ledger_registry.py` が自分の一覧に持つ名前で reader 判定される |
| import のみ（読み関数を呼ばない） | 1 | |

### 偽陰性の型（214件）
| 型 | 件数 |
|---|---|
| **public API / wrapper 経由** | **214（全部）** |

★**偽陰性は100%が「公開関数経由で読んでいるが basename を書かない」**。
「変数経由で開く」は Owner 側の話であって、★真の問題は**読み手が台帳名を書かない**こと。

## 4. ★対照（Taka 指定）— 的中した

> 「s10_ledger_registry.py が 13 CANONICAL 台帳すべての reader として誤検出されるかを最初の対照にする」

```
CANONICAL 13件中 ★13件すべてで 自己参照の偽陽性
（dev-workcell/data/pending_actor / dev-workcell/events / ds/ds_events /
  egl/DESIGN_EVIDENCE_LEDGER / egl/data/events / rri/rri/rthread_events /
  rri/rri_records / twoder/audit/ARTIFACT_REGISTRY / CHANGE_LOG /
  COMPLETION_DEFINITION_REGISTRY / ROADMAP_REGISTRY /
  twoder/failure_memory / failure_recurrence）
```
★`CANONICAL_LEDGERS` に列挙した**その行為自体が**、全 CANONICAL 台帳の reader 判定を汚染している。

## 5. 台帳ごとの偏り

| 台帳 | GT | 検出 | TP | FP | FN |
|---|---|---|---|---|---|
| `dev-workcell/events.jsonl` ほか `events.jsonl` 系 9件 | 19 | 43 | 9 | **34** | 10 |
| `ds/data/event_trace.jsonl` | 39 | 1 | 1 | 0 | **38** |
| `rri/rri/rthread_events.jsonl` | 12 | 2 | 1 | 1 | 11 |

★`events.jsonl` は **basename が同じ台帳が9本ある** ∴ 検出器は9本すべてに同じ43件を返す
（basename 一致では**どの台帳か区別できない**）。★これは precision と recall を同時に壊す。

★recall = 0 の台帳は **0件**（GT を持つ34台帳すべてで最低1件は当てている）。

## 6. まだやっていないこと
- 修正（この文書は**修正前の記録**）
- 修正後の precision / recall の再測定
- 既存 mismatch 判定（`--check`）への影響の再測定
- ★rthread だけ通る修理をしないこと（全台帳で一般化を確認する）

---

## 7. ★自己監査（2026-08-23）— ★§3 の数字を撤回する

Taka 指示「やろうとしていることが実際にその通りになった結果が今の結果なのか、
**そもそも作った測定器が壊れているのでその結果なのか**」に対する自己監査。

### ★計器の欠陥3件（すべて実測で確認）

| # | 欠陥 | 証拠 |
|---|---|---|
| ① | **本番と違う呼び方をしていた** | 本番は `readers(base, ow["programs"])` と**書き手を除外**して呼ぶ（`s10:270`）。私は `readers(base, [])` で呼び、**書き手を偽陽性に数えていた** |
| ② | **GT が書き手を「読み手」と数えていた** | `open(` を含むだけで読み関数扱い → `_append` / `open_thread` / `raise_question` など**12個の書き手**が read_funcs に混入。結果 `submit.py`（★書くだけ）が「真の reader」になっていた |
| ③ | **basename 衝突が私の GT にも効いていた** | 同 basename の台帳が **22本**（`events.jsonl` 9 / `REVIEW_LEDGER` 5 / `DESIGN_EVIDENCE_LEDGER` 4 / `audit_backlog` 4）。★**同じ計算を22回数えていた**（前回 FP 442 のうち **306件=69%** が重複） |

### ★訂正後の数字

| | precision | recall | TP | FP | FN |
|---|---|---|---|---|---|
| ~~§3 の報告（★壊れた計器）~~ | ~~0.280~~ | ~~0.446~~ | ~~172~~ | ~~442~~ | ~~214~~ |
| 訂正後（全56台帳） | **0.031** | **0.083** | 14 | 442 | 155 |
| 訂正後（★衝突22本を除く） | **0.024** | **0.017** | **1** | 41 | 59 |

★**検出器の品質は、私が報告した値よりはるかに悪い**のが正しい結論。
GT を「読み手だけ」に絞ると TP がほぼ消える（172 → 14 → 衝突除きで **1**）。
∴ ★**`readers()` は真の読み手をほとんど当てていない**。当たって見えたのは私が書き手を数えていたから。

### 変わらなかったもの（結論は保つ）
- 偽陽性の型と件数: comment/docstring のみ **329** ／ basename 直書きだが読まない **80**
  ／ **registry 自身の自己参照 32** ／ import のみ 1
- **偽陰性は100%が public API 経由**
- **CANONICAL 13件中13件で自己参照の偽陽性**（Taka 指定の対照）
- **basename 衝突 22本** ―― ★自己監査で**私の側にも同じ欠陥**があると分かり、重大性が上がった

### ★判定
- 「やろうとしたこと」＝ 検出器の品質を分母つきで測る → **やれている**
- 「その通りの結果か」＝ ★**いいえ。計器が壊れており、検出器を実際より良く見せていた**
- 欠陥の構造（4つの偽陽性型 / 偽陰性は API 経由100% / 自己参照 13-13 / basename 衝突22本）は
  **修正後も同じ**で、むしろ強まった ∴ **次へ進めてよい**

### ★修理の中心（判定の変更）
`basename` 衝突は **検出器と私の計器の両方に同じ欠陥**があった。
∴ 「別 AXIS に分ける」ではなく **修理の中心に据える**。
★`basename` を鍵にする限り、どちらも直らない（[[numbers-need-their-key]] の型）。
