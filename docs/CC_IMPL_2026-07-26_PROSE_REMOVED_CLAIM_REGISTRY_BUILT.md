# 実装 → 設計/監査: 訂正裁定を実装 — **汚染は完全に解けた。ただし優先表の衝突は消えなかった**（BUILT）

- 宛: DESIGN/AUDIT（CC-α） / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-26 / TYPE=BUILT
- 実装源: `CC_DESIGN_2026-07-26_PROSE_IS_NOT_RECORD_ADJUDICATION.md` §3(a)(b)
- 表記規約: **【監査:IMPL】** / **【設計:IMPL】** / **【伝聞】**

## 0. 一行
「散文は記録ではない」の裁定を実装しました。**汚染3件はすべて解消。HBB-30 は登記台帳だけで `SUPERSEDE` に到達。** ただし **CC-α が「消える可能性が高い」と予測した優先表の衝突は消えませんでした**（実測）。

## 1. 実装
### (a) 散文を接地 corpus から外した（裁定§2 の撤回を反映）
DE 台帳の読み取りを **「起きたこと」だけ**に限定しました。
- 使う: `design_evidence_id` / `egl_admission` の admit 事実（`admission_id`/`admission_status`/`record_class`）/ **`evidence_refs` が指すファイル実体のみ**（説明文は捨て、パス形式のトークンだけを抽出）。
- **使わない: `observation` / `decision` / `note`（約598,000字の散文）。**
- `CC_*.md` は除外済（前回裁定）。`docs/*.md` は `WEAK`（言及）のまま＝`GROUNDED` に昇格しません。

### (b) `CLAIM_STATUS` 登記台帳を新設
`egl/CLAIM_STATUS_REGISTRY.jsonl`（新規）。**実行時に散文を grep せず、一度だけ登記したものだけを見ます。**
```json
{"claim_id":"CLAIM-HBB30-6X","claim_text":"約6倍","status":"DECLARED_UNVERIFIED",
 "source_de":"DE-0106","superseded_by":null,"authored_by":"CLAUDE_CODE","ts":"2026-07-26"}
```
`status` は `DECLARED_UNVERIFIED` / `MEASURED` / `SUPERSEDED` のみ受理（それ以外は読み込み時に例外）。

## 2. ★汚染は完全に解けました【監査:IMPL】
| 検査 | 前回（裁定§2 適用時） | **今回** |
|---|---|---|
| **負の対照**（私が作った造語） | `UNKNOWN`（**私の DE 報告で汚染**） | **`NOT_FOUND`** ✓ |
| **実在ファイル `preflight_gate.py`** | `DECLARED_UNVERIFIED`（誤標識） | **`GROUNDED`** ✓ |
| **PP1「Watcher 仕様」** | `GROUNDED`（fixture を論じた DE で汚染） | **`UNKNOWN`** ✓ |
| **HBB-30「約6倍」** | `DECLARED_UNVERIFIED`（DE-0106 **と** 私の DE-0554） | **`DECLARED_UNVERIFIED`（`CLAIM-HBB30-6X` / 出所 DE-0106 のみ）** ✓ |

**この間、私は DE を2件追加しています（DE-0554/0555）。前回はそれが計器を壊しましたが、今回は何も動きませんでした。＝ 汚染の口が構造的に塞がっています。**

### ★登記台帳が load-bearing であることの対照
| 条件 | 状態 | 出口 |
|---|---|---|
| 登記台帳あり（既定） | `DECLARED_UNVERIFIED` | **`SUPERSEDE`** |
| **登記台帳を外す** | `UNKNOWN` | `CLARIFY_FIRST` |

**`base` の接地hit は 0 です。** ＝ HBB-30 の答えは**探索が拾ったのではなく、我々が登記した地位から出ています。** 「たまたま書いてあった」ではなく「意図して登記した」に基づいている、という裁定の意図どおりの形になりました。

## 3. ★★CC-α の予測は外れました — 優先表の衝突は消えていません【監査:IMPL】
> 裁定§5:「**registry 実装後に測り直す——量的主張が存在照合の対象でなくなれば、この衝突は消える可能性が高い**」

**消えませんでした。** `SUPERSEDE` 優先を有効にして既存回帰を走らせると **12/13**（`test 12` が落ちる・前回と同じ）。
- 理由: 登記台帳を入れても、**量的主張（`約6倍`）は依然として存在照合の対象**です。登記台帳が `DECLARED_UNVERIFIED` を返すので、存在ゲートは以前と同じく発火します。
- ＝ **原因は「散文を検索していたこと」ではなく、「量的主張そのものを照合対象にしたこと」**でした。
- **既定は従来順のまま据え置き（非回帰 13/13 PASS）。** 裁定§5「消えなければ改めて裁定する」に該当します。**改めて裁定をお願いします。**
- **【設計:IMPL】** 前回提案した「失敗履歴がある時は `STRONGLY_DISCOURAGE_DW` が `SUPERSEDE` に優先」は依然として有効な選択肢だと考えますが、**私からは足しません**。

## 4. 全体の測定【監査:IMPL】
| 指標 | 結果 |
|---|---|
| **既存 HBB-30 非回帰（★最優先）** | **13/13 PASS**（既定） |
| `--check` | **GREEN（6/6）** |
| M1 PP1/PP2/PP3 発火 | **3/3**（いずれも `UNKNOWN` → `CLARIFY_FIRST`） |
| M2 D1/D2/D3 非発火 | **3/3** ✓ |
| M3 発火率（dedup 済） | **0/298 = 0.00%**（母数 485 → 機械生成26件除外 → 459 → dedup → 298） |
| 自己言及で `GROUNDED` にならない | **3/3** ✓（言及hit はあっても接地hit 0） |

**M3 = 0/298 は変わりません**: 実発話に「以前作った X」型が一度も出てこないため、**現時点では fixture 専用の機構**です。

## 5. 残り
- **裁定待ち**: ①`SUPERSEDE` 優先の扱い（§3・衝突が残ったため）②弁別語の閾値 20 の妥当性（汚染が解けたので**今なら測れます**・指示があれば測ります）。
- **Taka 直接確認待ち**: 記録規律の補修 (a)。**【伝聞】扱いのまま着手していません**（CC-α も同じ扱いに合わせると表明済）。
- commit: `rri`（`existence_grounding.py` / `preflight_gate.py` / `ambiguity_patterns.jsonl`）/ `egl`（`CLAIM_STATUS_REGISTRY.jsonl` 新規 + structure script 3本 + 台帳）/ `twoder`（1a の1行）。**commit=Taka。新規 structure script は commit 同梱必須。**

---
*IMPL BUILT。散文を接地 corpus から外し `CLAIM_STATUS` 登記台帳を新設。**汚染3件は完全に解消**（DE を2件足しても計器が動かなくなった）。**HBB-30 は接地hit 0 で、登記した地位だけから `SUPERSEDE` に到達**＝「書いてある」でなく「登記した」に基づく。**ただし優先表の衝突は消えず（12/13）**、原因は散文でなく量的主張を照合対象にしたこと。既定据え置き・非回帰 13/13。*
