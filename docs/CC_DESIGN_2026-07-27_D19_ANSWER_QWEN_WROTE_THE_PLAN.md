# 設計/監査 → MGR（写: Taka / IMPL）: **D-19 の答え — Qwen が書いた。決定論テンプレは front door 由来の task では原理的に発火しない**

- `BUILD_ROLE: 参照`
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.7）**
- **受領した文書**: `CC_MGR_2026-07-27_BUILD11_RECEIVED_WHO_WROTE_THE_PLAN.md`(D-19)
- 併読: `CC_DESIGN_2026-07-27_BUILD11_AUDIT.md`（**MGR 未読。§2 が D-19 の半分を先に答えている**）

## 0. 答え（先に）
| MGR の問い | 答え |
|---|---|
| `auto_served: None` の意味 | **★値が `None` なのではない。`/api/run_next` の応答に `auto_served` が入っていない**（webui が転送しない） |
| `planner_outcome: null` の意味 | **★`.get()` の既定値。** 成功パスの early return は `planner_outcome` を持たない |
| **PLAN を書いたのは誰か** | **★Qwen `BUILD_PLANNER` である。** 決定論テンプレは、**front door 由来の task では原理的に発火しない** |

**★台帳を読んでいない。新しい実行もしていない。すべてコード構造からの導出である**（v1.3 §2-1 の許可範囲）。

---

## 1. `dispatched: true` が成り立つ経路は2つしかない【監査:CC-α】
```
再現: sed -n '74,120p' dev-workcell/dw/dispatch.py
```
| 行 | 条件 | 戻り |
|---|---|---|
| :79-80 | `op in ("NONE","BLOCKED")` | `dispatched: False` |
| :84-91 | **`op == "DISPOSE"`** かつ機械処理可能 | `dispatched: True`（**本件は `op == "PLAN"` なので該当しない**） |
| **:97-101** | **`PT.plannable(task_id)`** | **`dispatched: True` / `auto_served: RULE_TEMPLATE_PLAN` / identity `2der-auto-plan-template`** |
| **:114-116** | **Qwen planner が `recorded: True`** | **`dispatched: True` / `auto_served: QWEN_BUILD_PLANNER` / identity `2der-qwen-build-planner`** |
| :123-126 | 上記以外（`claude_barrier` は `CREATED` で **True**） | `dispatched: False` / `CLAUDE_BARRIER` |

**∴ `op == "PLAN"` で `dispatched: true` になるのは、テンプレか Qwen の2つだけである。**

---

## 2. ★テンプレは発火し得ない（front door 由来の kp の形から決まる）【監査:CC-α】

```
再現: sed -n '23,36p' dev-workcell/dw/plan_template.py     # is_bounded_reproduction_candidate
再現: sed -n '424,429p' twoder/submit.py                   # front door が作る kp
```

**判定式（逐語）:**
```python
obj       = (kp.get("object_type") or kp.get("packet_type") or "")
objective = ((kp.get("experiment") or {}).get("objective") or "").lower()
rb        = (kp.get("rollback_reference") or {}).get("plan") or []
first     = (rb[0].lower() if rb else "")
return bool(obj == "DW_EXPERIMENT_CANDIDATE" or "reproduce" in objective or "read-only reproduction" in first)
```

**front door が作る kp（`submit.py:424-429`）が持つキー:**
```
packet_type / schema_version / task_context / current_claims / admitted_claims / reported_claims /
historical_claims / open_gaps / related_failure_patterns / non_guarantees / source_trace / provenance
```

| 判定項 | front door の kp では |
|---|---|
| `obj == "DW_EXPERIMENT_CANDIDATE"` | **偽**。`packet_type` は **`"KNOWLEDGE_PACKET"`** 固定 |
| `"reproduce" in objective` | **偽**。**`experiment` キーが存在しない** → `objective` は空文字 |
| `"read-only reproduction" in first` | **偽**。**`rollback_reference` キーが存在しない** → `first` は空文字 |

> **∴ `is_bounded_reproduction_candidate` は、front door 由来の task に対して常に False を返す。**
> **∴ `PT.plannable` は常に False。∴ テンプレ経路は発火しない。**
> **∴ 残るのは Qwen `BUILD_PLANNER` のみである。**

**★これは本件だけの話ではない。** **`submit()` から作られる task では、決定論テンプレの PLAN は構造上ありえない。**
**∴ front door 由来の task の PLAN は、成功すれば必ず Qwen が書いている。**

### 2-1. なお `source_trace` が非空でも結論は変わらない
判定式の第1関門（`finding_ids or source_trace` が非空）は通り得る（Build 9C で `egl_source_refs: ["DE-0484"]` が観測されている）。
**しかし第2関門の3条件がすべて偽なので、結論は変わらない。** **「通ったから発火する」ではない。**

---

## 3. ★私はこの結論を「観測」とは呼ばない【監査:CC-α】
- **これはコードからの導出である。** **実行して確かめていない。**
- **決定的な確認は1つ**: **DW の `PLAN` イベントに記録された identity**（`2der-auto-plan-template` か `2der-qwen-build-planner` か）。
- **私はそれを読んでいない**（台帳の中身であり、`【直読】` になるため）。**IMPL 側は `derive_state` を既に叩いているので、そこから1行で出せる。**
- **★導出と観測が食い違ったら、観測が正しい。** **私の §2 が誤っているということになるので、そう書く。**

---

## 4. MGR の「Qwen が書いたと読み替えない」について
**MGR の指示は正しかった。** **`auto_served: None` から「Qwen が書いた」は言えない。**
**私が言えるのは、別の根拠からである**——**`auto_served` を見ずに、テンプレ経路が発火し得ないことを示した。**
**∴ 結論は同じでも、根拠が違う。** **本日2回「当たったが理由が違う」をやっているので、根拠の側を明示しておく。**

---

## 5. 併せて（Build 11 監査で既報・MGR 未読）
1. **実証されたのは S3 のみ。** S1（dispatch 側）は成功パスでは値が流れないため未実証。**`planner_outcome: null` は S1 が有っても無くても同じ。**
2. **`auto_served` は4つ目の捨て場所。** dispatch は返しているが webui が転送しない。**Build 10 で「3つ」と数えたとき、私が見落とした。**
3. **提案 B**（`auto_served` を `/api/run_next` の応答に載せる・追加のみ）を出してある。**これが入れば、次から「誰が書いたか」は導出でなく観測になる。**

---

## 6. 残（消さない）
| 件 | 状態 |
|---|---|
| **PLAN の identity による確認** | **未実施**（§3） |
| **S1 の実証** | **未。** PLAN が失敗したときにしか確かめられない |
| `auto_served` の転送（提案 B） | 未着手・裁定待ち |
| PLAN の中身が使えるか | **未評価**（MGR §4 のとおり D-19 の後） |
| オラクル | **未開封**（sha256 `77af566…`）。`ids.resolve()` 未実行 |

---
*CC-α D-19 の答え。★PLAN を書いたのは Qwen `BUILD_PLANNER` である——台帳を読まず、新しい実行もせず、コード構造から導出した。①`op == "PLAN"` で `dispatched: true` になる経路はテンプレ(:97-101)と Qwen(:114-116)の2つだけ（DISPOSE の自動処理は op が違い、それ以外は `CREATED` の `claude_barrier=True` により barrier）。②★テンプレは front door 由来の task では原理的に発火しない——`is_bounded_reproduction_candidate` の3条件は `packet_type="KNOWLEDGE_PACKET"` 固定・`experiment` キー無し・`rollback_reference` キー無しにより全て偽になる（`submit.py:424-429` の kp の形から決まる）。∴ `submit()` 由来の task の PLAN は、成功すれば必ず Qwen が書いている。`source_trace` が非空でも第2関門で落ちるので結論は変わらない。★`auto_served: None` は値が None なのではなく webui が転送していない、`planner_outcome: null` は成功パスの early return にキーが無く `.get()` の既定値が出ている。★これは導出であって観測ではない——決定的な確認は DW の PLAN イベントの identity(`2der-auto-plan-template` か `2der-qwen-build-planner`)で、私は台帳を読んでいないので IMPL 側に1行で出せる。導出と観測が食い違えば観測が正しく、私の §2 が誤っていることになる。MGR の「読み替えない」指示は正しく、私は `auto_served` を使わずに別根拠で示した。*
