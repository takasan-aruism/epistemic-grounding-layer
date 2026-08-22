# 追補2 — `ESDE_INTEGRATION_ARCHITECTURE` ／ ★READER は在った。前例が本線で回っている

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
本体 `2b7812b` ／ 追補1 `1c0fe5f`・`aae3e46`・`dd4b6e2`
**★コードは1行も変えていない。★実装0。**
測ったHEAD: twoder `8b64b1f` / dev-workcell `68c3b4c` / egl `dd4b6e2`

---

## 0. ★訂正5 ―― 「READER が MISSING」は**誤り**だった

本体 §6 と追補1 §4 で私は「ESDE 評価結果を読む側は現在1つも存在しない ＝ MISSING」と書き、
**それを理由に実装差分を出さなかった**（Taka §6「writer あり / reader なし を作ってはならない」）。

**探し方が足りなかった。**「ESDE 評価結果」という名前で探したので0件になった。
**作用（構造の測定結果を読んで判断し記録する）で探し直したら、本線で回っている前例が在った。**
正本 §10②「名前だけでなく作用を起点に検索する」を、私自身が守れていなかった。

---

## 1. ★前例 ―― `domain_dw.record_stages()`（実測・本線・常駐）

**ESDE 評価に必要な7要素が、すべて1つの実装に揃っている。**

```python
# twoder/domain_dw.py:455-469（逐語）
oe = _call("/api/control?include=observed_edges&lookup_kind=verify&caller=MANAGER_V0.refresh",
           timeout=460)["observed_edges"]
observed = [str(k).split(".")[0] for k in ((oe.get("direct_counts") or {}).get("by") or {})]
segs     = (oe.get("segments_from_records") or {}).get("rows") or []
used     = [str(x.get("to") or "").split(".")[0] for x in segs if x.get("evidence") == "BOTH"]
r = _use("stage_from_evidence", stage_from_evidence, placed, observed, used, part_of)
...
_ET.emit("CONTRACT_STAGE", "reached",
         {"why": row["why"], "key_note": "証拠から 決めた(★自己申告 0)"},
         {"stage": row["stage"]}, "OK", task_id=row["task_id"], fail_open=True)
```

| 要素 | この前例での実体 | 状態 |
|---|---|---|
| **IDENTITY** | `task_id`（既存 ID）＋ `stage` | **PRESENT** |
| **CALLER** | `manager_v0.main()` の巡回（`record_stages` は毎周の先頭） | **OBSERVED** |
| **TIMING** | Manager 巡回の**記録段**（`INTERVAL=60`） | **OBSERVED** |
| **INPUT** | front door `/api/control?include=observed_edges`（★台帳直読でない） | **OBSERVED** |
| **判定器** | `stage_from_evidence`(**2DER 製**)。`_use(...)` で包んで呼ぶ | **OBSERVED** |
| **OUTPUT** | `{stage, why}` ＋ **`no_evidence` を落とさず持つ** | **PRESENT** |
| **STORAGE** | 既存 ETRACE の `CONTRACT_STAGE` kind（**新台帳0**） | **OBSERVED** |
| **READER** | Manager 自身（`out["rows"] / by_stage / no_evidence` を手番判断へ） | **PRESENT** |
| **AUTHORITY** | **何も止めない・何も承認しない。記録するだけ** | **PRESENT** |

**★逐語「証拠から 決めた(★自己申告 0)」は、正本 §14「機械取得不能な値を LLM 自己申告で埋めない」
と同じことを、実装が既にやっている。**

**∴ ESDE 評価の統合は「新しい機構を作る」問題ではない。`record_stages` と同じ形を取る問題。**

---

## 2. ★もう1つの前例 ―― `route_worker.self_check()`（自律的調査の最小形）

Taka の目的「**ESDE アーキテクチャ的な自律的な調査基盤**」に、**既に最小形が在る**。

```python
# twoder/route_worker.py:113-116（逐語 docstring）
"""★同じ問いを 2回 引いて ★動いた欄を 名指しする。★判定の語は 出さない。
   ★これが 見つける物 = ★『見ると 増える 計器』(★引く 行為が 数に 入っている 欄)。
   ★判定 = twoder/unstable_keys.py（★2DER が 書いた・★1行も 書き換えていない）"""
```

| 観点 | 実測 |
|---|---|
| 調べる面 | `SELF_CHECK_INCLUDES` **14面**（route_table / authority_summary / anatomist / static_edges / edge_measures / observed_edges / function_table / function_index / function_first ほか） |
| 方法 | **同じ問いを2回引いて差分**（★観測が観測対象を汚していないかの検査） |
| 判定 | `unstable_keys.py` ―― **2DER が書いた・Claude は1行も書き換えていない** |
| 除外 | `SELF_CHECK_IGNORE`（`*.ts` `*.as_of` 等）。逐語「★除いた物は 名前で 残す(★黙って 除かない)」 |
| 保存 | `twoder/runs/self_check.json`（`os.replace` で原子的） |
| 記録 | `ETRACE.emit("ROUTE_WORKER","self_check", ...)` |
| **READER** | **`webui.py:1087`** が `RUNS/"self_check.json"` を読む ∴ **front door から見える** |
| 呼び手 | `route_worker.py:278` 常駐ループ ＋ `:293` CLI |

**★これは「2DER が自分の計器を疑う」機構。ESDE の対等性検査そのものではないが、
『判定を LLM でなく 2DER 製の決定論に置く』『除いたものを名前で残す』は正本と同型。**

### さらに ―― 計器が自分の出力を点検している

```python
# twoder/observed_edges.py:441,446-447（逐語）
# ★★計器が ★自分の 出力を 点検する(★2DER の `self_check_signals` を ★自動で 呼ぶ)
from twoder.self_check_signals import self_check_signals as _scs
_prev_p = os.path.join("/home/takasan","twoder","runs","self_check_prev.json")
```

**`self_check_prev.json` が在る ＝ before/after を比較する機構が既存。**
正本 §10⑩「変更後に同じ因果鎖・同じ試験で before/after を測る」の**器は既に在る**。

---

## 3. ★訂正6 ―― 追補1 §1 の「述語で問える引数が0」は**測り方が雑だった**

追補1 では route 先頭から**1,400字の窓**だけを見て引数を抽出した。
`/api/control` は **339行**あるので、窓の外を見落とした。**測り直した。**

**測り直しの方法**: `if u.path ==/in` の出現位置**20箇所**で本文を区切り、
**各 route の全長**から `q.get("...")` を抽出（★窓を使わない）。

```
16口 / 引数18種
★識別子以外の引数 = 2つだけ ―― どちらも /api/control の function と lookup_kind
```

**その2つを実際に読んだ結果、どちらも述語ではなかった：**

```
function      function_table.function_index(name) → hits = [r for r in _rows() if r.get("name") == name]
              ★完全一致。∴ 識別子引きと同じ。
lookup_kind   webui.py:1346 逐語「★呼び手の自己申告(★証拠にしない)」
              ★結果を絞らない。ETRACE の emit に載るだけ。
```

**∴ 結論は変わらない ―― 16口・引数18種のうち、結果を条件で絞れるものは 0。
ただし追補1 の「識別子以外が0」という書き方は誤りだったので訂正する。**

---

## 4. 9項目の更新（★本体・追補1 からの差分）

| 項目 | 本体/追補1 | **本追補2** | 根拠 |
|---|---|---|---|
| IDENTITY | PRESENT（`function_table` 候補） | **PRESENT** ―― ★候補が変わった: `task_id` ＋ 段の語（`record_stages` 方式） | §1 |
| CALLER | Manager 側（絞り込み） | **OBSERVED** `manager_v0.main()` 巡回 | §1 |
| TIMING | UNVERIFIED | **OBSERVED** Manager 巡回の記録段（`INTERVAL=60`） | §1 |
| INPUT | PRESENT | **OBSERVED** `/api/control?include=` 経由（★直読でない） | §1 |
| OUTPUT | UNVERIFIED | **PRESENT（前例あり）** `{stage, why}` ＋ `no_evidence` を落とさない | §1 |
| STORAGE | PRESENT（候補） | **OBSERVED** 既存 ETRACE の kind を1つ使う（新台帳0） | §1 |
| **READER** | **MISSING** | **★PRESENT ―― 訂正。Manager 自身が読んでいる** | §1 |
| AUTHORITY | UNVERIFIED | **PRESENT（前例あり）** ―― **何も止めない・記録だけ** | §1 |
| TEST | 未定義 | 計画済（本体 §8 の6項目） | 本体 |
| QUERY_SURFACE | ABSENT | **ABSENT（維持・証拠を正した）** | §3 |
| CANON_NOT_IN_LEDGER | MISSING | **解消**（`ART-fd56608eab` / `ART-53632b55e4`） | 追補1 |

---

## 5. ESDE 宣言（正本 §12・★対象＝統合の形）

```
AXIS: ESDE_EVALUATION_FOLLOWS_RECORD_STAGES_SHAPE
SCOPE:
  entry:       Manager 巡回が front door から構造の測定を読む
  exit:        2DER 製の判定器が結果を出し、既存 ETRACE に記録される（★Claude を経由しない）
  authority:   発行 0・変更 0（★前例も何も止めていない）
  persistence: 新台帳 0（既存 ETRACE の kind を1つ）
  components:  manager_v0.main / domain_dw.record_stages / /api/control /
               observed_edges / stage_from_evidence / ETRACE / route_worker.self_check /
               unstable_keys / self_check_signals

EQUALITY   canonical: 「構造の測定を読んで判断し記録する」形
           compatible:   [record_stages（★本線・OBSERVED）, self_check（★常駐・OBSERVED）,
                          observed_edges の自己点検（OBSERVED）]
           incompatible: []
           unknown:      [ESDE の6概念を この形に載せた時の欄]
           status: ★PRESENT（★前例が3つ在る）

SYMMETRY   pairs: [測る側 ↔ 読む側, 記録する側 ↔ 引く側, 判定器 ↔ 除外規則]
           required 3 / present 3 / missing 0 / unverified 0
           ★record_stages: 測る=observed_edges / 読む=Manager
           ★self_check:    記録=runs/self_check.json / 引く=webui.py:1087
           ★判定器=unstable_keys ↔ 除外=SELF_CHECK_IGNORE（★名前で残す）

LINKAGE    edges:
             E1 Manager巡回 → /api/control            status: OBSERVED（domain_dw:455）
             E2 /api/control → 測定結果               status: OBSERVED
             E3 測定結果 → 2DER製の判定器             status: OBSERVED（stage_from_evidence）
             E4 判定器 → ETRACE                       status: OBSERVED（CONTRACT_STAGE reached）
             E5 ETRACE → Manager の手番判断           status: ★UNVERIFIED（読んでいるが影響を測っていない）
           declared 5 / observed 4 / broken 0 / unverified 1

HIERARCHY  boundaries: [front door 単一入口, 台帳直読の禁止, authority 境界,
                        Route Worker に Manager の責務を足さない]
           required 4 / passed 4 / violation 0 / unreachable 0
           ★前例は4つとも守っている。★特に「記録するだけで何も止めない」= authority を増やしていない。

R1_END_TO_END      status: ★OBSERVED（★但し ESDE 評価ではなく「段の判定」で）
                   evidence: domain_dw:455-469 が本線で回っている（manager_v0 常駐）
R2_DENOMINATOR     required: ESDE 評価の7要素 ／ observed: ★7/7 に前例あり ／ status: PRESENT
                   ★但し「前例が在る」であって「ESDE 評価が動いた」ではない
R3_INTERNAL_GATES  gates: [front door 認証, caller 名乗り, include の語の検査(未知語はエラーを返す)]
                   passed: [認証(実確認)] / failed: [] / unverified: [caller, include 検査]
R4_REJECTION       rejection_conditions: [★未列挙] / status: ★UNVERIFIED

UNDERSTANDING  candidate: ESDE_EVALUATION_FOLLOWS_RECORD_STAGES_SHAPE
               requires: [7要素の前例（★満たした）, 述語の口（★ABSENT）, 実走]
               evidence: [§1 の7/7, §2 の self_check]
               unresolved: [★調査面の不在（§3）が残る ―― 正本§10② を 2DER が実行できない]
               result: ★UNKNOWN（★ESTABLISHED にしない）

CREATION   status: NOT_EVALUATED
DECISION   ★DESIGN_HOLD（★但し理由が変わった）
```

---

## 6. ★DESIGN_HOLD の理由が変わった

```
本体・追補1 の理由  ① READER が MISSING       → ★解消（§1）
                    ② 口の形が推測でしか埋まらない → ★解消（record_stages の形を取る）

本追補2 の理由      ★正本§10② の全件調査を 2DER が実行できない（§3・述語の口が0）
                    ∴ ESDE 評価を載せても、材料を集める工程が Claude のまま残る。
                    ★「Claude 破棄」の観点では、ここを飛ばすと律速が動かない。
```

**∴ 次に確定すべきは「述語で問える口」―― ただし ★新しい口を作らない前提で、
既存の `include=` 面（14面）で どこまで答えられるかを先に測る。**
`SELF_CHECK_INCLUDES` が既に14面を列挙しているので、**分母は在る。**

---

## 7. 触っていないもの

`EVO-0085` writer 4欠損 ／ `EVO-0087` 呼び手0 ／ `EVO-0088` harness fixture ／
並行運用 `EVO-0084` ／ 正本§13 の UNVERIFIED 差戻し ／ REARM 263 ／ `_GATES_MAX` ／
`esde/ESDE-Research`（★Taka 裁定により**無視**）。
