# 設計/監査 → MGR（写: Taka / IMPL）: **D-116 — DE 下書き（P-1・1件）。★まだ呼んでいない。★承認をください**

- `BUILD_ROLE: 参照`（**下書きのみ。★1回も呼んでいない・★実装していない・★台帳を直読していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-30 / TYPE=FINDING
- **裁定**: `CC_MGR_2026-07-30_D115_DRAFT_THEN_APPROVE_THEN_CALL.md` §3（★①下書き ②承認 ③IMPL が呼ぶ）

## 0. ★2DER 優先原則の5点
| ① 入口 | **★`egl/structure/de_submit_route.py::record_de`**（★既定＝front door／submit 経由） |
|---|---|
| ② 何を試したか | **★まだ試していない**（★下書きの段。★呼んでいない） |
| ③ できなかったこと | **★該当しない**（★呼ぶ前である） |
| ④ 何を実装するか | **★何も実装しない。★既に在る口を1回 使うだけ** |
| ⑤ | **★呼んだ後に IMPL が書く** |

## 1. ★呼び方（★1行・★route を指定しない）
```
record_de(candidate)          ★route 未指定 ＝ 既定 "submit"（front door 経由）
★`route="direct"` を使わない。★`DE_ROUTE` を export しない。★`ledger_path` を渡さない（既定＝本番）
```

## 2. ★candidate の下書き（★これがそのまま入る）
```json
{
  "observation": "Phase 3 P-1: 「届いたか」を 2DER に聞ける口を1つ作った(GET /api/receipt)。返りは last_recv_at / recv_count / last_sent_at / last_sent_status / readable の5欄で、log の行そのものは返さない。measured(CC-α 実測): 受入13件を1つずつ確認し、返る欄が5つだけ・仕様外0件、返り値に RECV/SENT/api を含む文字列が0件、recv_count と readable が別の欄、配信物の <script> 19854 バイトが node --check を通る。measured(CC-α 実測): CC-α は submit_access.log を1行も読まずに「直近の受信 2026-07-30T12:53:07.133501 / これまでに 67件」と答えた(60秒 空けて2回とも同値)。MGR も同様に log を読まずに答えたと申告している。★「あの送信が届いたか」は答えられない — 受信記録に依頼を特定する id が無いため。★67件のうち誰が送ったかは出せない。",
  "decision": "「届いたか」だけを返す口を1つ作り、log の行そのものは返さない(数と時刻だけ)。受信記録に id を足すのは本 build で行わず別件として据え置く。「届いたかが分かるようになった」とは書かない(1件ごとには分からないため)。",
  "decision_owner": "Taka (Phase 3 P-1 の指示) / MGR (裁定・受入条件の訂正・commit) / CC-α (BUILD SPEC・受入確認) / IMPL (実装)",
  "evidence_refs": [
    "commit twoder f32e6b1",
    "measured: GET /api/receipt -> {last_recv_at: 2026-07-30T12:53:07.133501, recv_count: 67, last_sent_at: 2026-07-30T12:53:11.089193, last_sent_status: 200, readable: true} (CC-α 実測・2回とも同値)",
    "measured: 配信物の <script> 19854 バイトが node --check を通る (CC-α 実測)",
    "measured: /api/tasks は 155件のまま (CC-α 実測・本日3回)",
    "docs/CC_DESIGN_2026-07-30_D102_P1_ASK_2DER_IF_IT_ARRIVED_SPEC_v1_0.md",
    "docs/CC_IMPL_2026-07-30_D102_P1_ASK_2DER_IF_IT_ARRIVED_BUILT.md",
    "docs/CC_DESIGN_2026-07-30_D103_P1_ACCEPTED_AND_THE_INSTRUMENT_FOUND_SEVEN_WE_DID_NOT_KNOW.md"
  ],
  "claimed_status": "OBSERVED",
  "generated_by_principal": "CLAUDE_CODE"
}
```

## 3. ★MGR の表に無いものを2つ入れた（★理由を書く）
| 欄 | ★理由 |
|---|---|
| **`decision` / `decision_owner`** | **★スキーマの必須項目である**（`de_admission.py:22 REQUIRED = ("observation","decision","decision_owner")`）。**★無いと弾かれる** |
| **`claimed_status: "OBSERVED"`** | **★入れなくても `evidence_refs` に `measured` が在るので OBSERVED になる**（`_record_class`）。**★明示して、推測で決まらないようにした** |

## 4. ★入れなかったもの（★理由を書く）
| 欄 | ★理由 |
|---|---|
| **`generation_mode`** | **★MGR の表に無い。★私は5つの語（`DIRECT`/`MANUAL_SUBSTITUTION`/`TRANSPORT_ONLY`/`COMMAND_RELAY`/`INSPECTION_ONLY`）の意味を確かめていない** ∴ **★推測で入れない** |
| **`fi_min_finding`** | **★同じく意味を確かめていない** |
> **★「入れられる欄は全部 埋める」をしない。** **★意味が分からない欄に、それらしい値を入れない。**

## 5. ★禁止語に当たっていないか（★自分で確かめた）
```
再現（★実装の定数と突き合わせた）:
  HARD_REJECT（18語: "self-improving" "proven correct" "fully verified" 等）→ ★下書きに ★0件
  BEHAVIORAL_MARKERS（"works in production" "verified live behaviour" 等）→ ★下書きに ★0件
∴ ★downgrade（ADMITTED → REPORTED）に当たる語も入れていない
```

## 6. ★中身が実在のものだけか（★1つずつ）
| # | 書いたこと | ★実在の根拠 |
|---|---|---|
| 1 | 口を作った | **commit `twoder f32e6b1`** |
| 2 | 返る欄は5つ | **★私が叩いて確認**（D-103） |
| 3 | 行を返さない | **★私が返り値を走査して0件**（D-103） |
| 4 | `node --check` を通る | **★私が実行**（19854バイト） |
| 5 | log を読まずに答えた | **★私が実行**（★2回とも同値） |
| 6 | MGR も答えた | **★MGR の申告と明記した**（★私は確かめていない） |
| 7 | 1件ごとには分からない | **★`RECV` の行に id が無い**（★実装を読んだ） |
| 8 | 67件の出所は出せない | **★口が返さない**（D-104） |

> **★6 だけが伝聞である。** **★「MGR も同様に申告している」と書き、★事実として書いていない。**

## 7. ★お願い
| # | |
|---|---|
| **1** | **★中身を承認してください**（★実在のものだけか／★1件か／★語を作っていないか） |
| **2** | **★承認後、★IMPL が `record_de(candidate)` を1回 呼ぶ**（★私は呼ばない） |
| **3** | **★呼んだ後、★返った `design_evidence_id` を front door から引いて、★`generated_by_principal` が `CLAUDE_CODE` で入ったかを★私が確かめる** |

> **★3 が本件の目的である。** **★入れることではなく、★⑭が動くかを見ることである。**

## 8. ★私が確かめていないこと
| # | | |
|---|---|---|
| 1 | **`record_de` が実際に動くか** | **★呼んでいない** |
| 2 | **submit 経由にすると DS/RRI に何が増えるか** | **★docstring に「DS→RRI→residual→DS thread を回す」と在る。★中身は読んでいない** |
| 3 | **`observation` の長さに制限が在るか** | **★確かめていない**（★下書きは約600字） |

---
*CC-α D-116（下書きのみ・1回も呼んでいない）。★**呼び方は `record_de(candidate)` で route を指定せず既定 "submit"（front door 経由）**、**`route="direct"` も `DE_ROUTE` の export も `ledger_path` の指定もしない**。★**candidate の下書き**=`observation`（P-1 で口を作ったこと・返る5欄・行を返さないこと・CC-α 実測の受入13件・**log を1行も読まずに「直近 2026-07-30T12:53:07.133501／67件」と2回とも同値で答えたこと**・**「あの送信が届いたか」は id が無いので答えられないこと**・**67件の出所は出せないこと**）／`decision`／`decision_owner`（Taka・MGR・CC-α・IMPL の役割）／`evidence_refs`（**commit `twoder f32e6b1`**・measured 3件・文書3件）／`claimed_status: "OBSERVED"`／**`generated_by_principal: "CLAUDE_CODE"`**。★**MGR の表に無いものを2つ入れた理由**=`decision`/`decision_owner` は**スキーマの必須項目**（`de_admission.py:22`）で無いと弾かれる／`claimed_status` は**入れなくても OBSERVED になるが明示して推測で決まらないようにした**。★**入れなかったもの**=`generation_mode` と `fi_min_finding` は**5つの語の意味を確かめていないので推測で入れない**——**「入れられる欄は全部 埋める」をしない。意味が分からない欄にそれらしい値を入れない**。★**禁止語の自己確認**=`HARD_REJECT`（18語）**0件**／`BEHAVIORAL_MARKERS`**0件** ∴ **downgrade に当たる語も入れていない**。★**中身が実在のものかを8点ずつ確認**し、**6（MGR も log を読まずに答えた）だけが伝聞なので「MGR の申告と明記」して事実として書いていない**。★**お願い**=①中身の承認 ②**承認後 IMPL が `record_de(candidate)` を1回 呼ぶ（CC-α は呼ばない）** ③**呼んだ後 返った `design_evidence_id` を front door から引き `generated_by_principal` が `CLAUDE_CODE` で入ったかを CC-α が確かめる**——**③が本件の目的であり、入れることではなく⑭が動くかを見ることである**。★確かめていないこと=`record_de` が実際に動くか（呼んでいない）／**submit 経由にすると DS/RRI に何が増えるか（docstring に「DS→RRI→residual→DS thread を回す」と在るが中身は読んでいない）**／`observation` の長さ制限（下書きは約600字）。*
