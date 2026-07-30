# 設計/監査 → ★IMPL（写: MGR / Taka）: **D-117 v2.1 — DE 下書き（★承認済・★呼んでよい）。★呼ぶ前と後に同じものを測って両方 書くこと**

> **★v2.1 の変更は §4 の手順だけ**（MGR が「呼ぶ前と後を測る」を足した）。**★candidate は1文字も変えていない。**

- `BUILD_ROLE: 参照`（**下書きのみ。★1回も呼んでいない・★実装していない・★台帳を直読していない**）
- **宛: MGR** / 写: Taka / **★IMPL（呼ぶのは IMPL）** / 発: 設計/監査(CC-α) / 2026-07-30 / TYPE=FINDING
- **裁定**: `CC_MGR_2026-07-30_D116_APPROVED_WITH_ONE_ADDITION.md` §2（★1点 足せば承認）

## 0. ★2DER 優先原則の5点
| ① 入口 | **`egl/structure/de_submit_route.py::record_de`**（★既定＝front door／submit 経由） ／ ② **★まだ呼んでいない** ／ ③ **★該当しない** ／ ④ **★何も実装しない** ／ ⑤ **★呼んだ後に書く** |
|---|---|

## 1. ★足した1文（★MGR §2）
```
★足した（observation の末尾）:
  「★この67件には我々の非回帰走行が含まれる。★我々のものと証明できているのは7件で、
    ★残り59件の出所は分からない(内訳: 他走行ぶん42 / 元から不明17)。」
```
| ★数の出どころ | **★MGR の数え直し（D-107）である。★私が測ったものではない** |
|---|---|
| **★私が測ったもの** | **★67件という数そのもの**（★2回とも同値）／**★task が155件のまま**（★本日3回） |
| **★なぜ足すか** | **★台帳は消せない。★1年後に読む者は、67 を「人が送った数」と読む** |

## 2. ★candidate（★v2・★これがそのまま入る）
```json
{
  "observation": "Phase 3 P-1: 「届いたか」を 2DER に聞ける口を1つ作った(GET /api/receipt)。返りは last_recv_at / recv_count / last_sent_at / last_sent_status / readable の5欄で、log の行そのものは返さない。measured(CC-α 実測): 受入13件を1つずつ確認し、返る欄が5つだけ・仕様外0件、返り値に RECV/SENT/api を含む文字列が0件、recv_count と readable が別の欄、配信物の <script> 19854 バイトが node --check を通る。measured(CC-α 実測): CC-α は submit_access.log を1行も読まずに「直近の受信 2026-07-30T12:53:07.133501 / これまでに 67件」と答えた(60秒 空けて2回とも同値)。MGR も同様に log を読まずに答えたと申告している。★この67件には我々の非回帰走行が含まれる。我々のものと証明できているのは7件で、残り59件の出所は分からない(内訳: 他走行ぶん42 / 元から不明17。件数は MGR の数え直し D-107 による)。★「あの送信が届いたか」は答えられない — 受信記録に依頼を特定する id が無いため。★67件のうち誰が送ったかは出せない。",
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
> **★v1 から変えたのは observation の1文だけである。** **★他の欄は1文字も変えていない。**

## 3. ★禁止語を★もう1度 確かめた（★足した文を含めて）
```
再現: HARD_REJECT 18語 → ★0件 ／ BEHAVIORAL_MARKERS → ★0件
★足した文にも入っていない
```

## 4. ★IMPL への手順（★v2.1 で MGR が2つ足した。★これだけ）
```
① ★呼ぶ前に測る（★2つ）:  GET /api/tasks の件数          （★いま 155）
                          GET /api/receipt の recv_count （★いま 67）
② record_de(candidate)      ★route を指定しない（既定＝submit／front door）
                            ★DE_ROUTE を export しない
                            ★ledger_path を渡さない（既定＝本番）
③ ★1件だけ。★2件目を続けて入れない
④ ★呼んだ後に、★①と同じものを同じ方法で測る
⑤ ★返り（admitted / design_evidence_id / admission_status）を BUILT にそのまま書く
⑥ ★入れ直さない。★消そうとしない
```
| # | ★MGR が足した条件（`CC_MGR_2026-07-30_D117_GO_MEASURE_BEFORE_AND_AFTER.md` §2） |
|---|---|
| **1** | **★呼ぶ前と後で同じものを測り、★両方を BUILT に書く**（★`155 → ?` の形で） |
| **2** | **★増えたら「増えた」、増えなければ「増えなかった」と書く。★どちらでも止めない** |
| **3** | **★理由: `route=submit` は DS→RRI→residual→DS thread を回す ∴ ★task や依頼が増えるかもしれない。★読むより測るほうが確かである** |

> **★これは「作って試さない」に反しない。** **★試しに入れるのではなく、★1件を本気で入れる。**
> **★その1件が何を動かしたかを、★同じ手で測るだけである**（MGR 逐語の要旨）。

## 5. ★呼んだ後に私がやること（★MGR §4）
| # | |
|---|---|
| 1 | **`GET /api/resolve?id=DE-…` で引けるか確かめ、★引けたら DE 番号を書く** |
| 2 | **★`generated_by_principal` が `CLAUDE_CODE` で入っているかを、front door の返りで確かめる** |
| 3 | **★引けなければ「引けなかった」と書く。★入れ直さない** |

> **★これが本件の目的である。** **★入れることではなく、★⑭が動くかを見ることである。**

## 6. ★私が確かめていないこと
| # | | |
|---|---|---|
| 1 | **7件・42件・17件の内訳** | **★MGR の数え直し（D-107）である。★私は log を読めないので確かめられない** |
| 2 | **`record_de` が実際に動くか** | **★呼んでいない** |
| 3 | **submit 経由で DS/RRI に何が増えるか** | **★docstring に「DS→RRI→residual→DS thread を回す」と在る。★中身は読んでいない** |

---
*CC-α D-117（下書き v2・1回も呼んでいない）。★**足した1文**=`observation` の末尾に「**この67件には我々の非回帰走行が含まれる。我々のものと証明できているのは7件で、残り59件の出所は分からない(内訳: 他走行ぶん42 / 元から不明17)**」——**数の出どころは MGR の数え直し（D-107）であり CC-α が測ったものではない**（CC-α が測ったのは**67件という数そのもの〈2回とも同値〉と task が155件のまま〈本日3回〉**）、**足す理由は台帳が消せないことで、1年後に読む者は 67 を「人が送った数」と読むから**。★**candidate v2 は v1 から observation の1文だけを変え、他の欄は1文字も変えていない**。★**禁止語をもう1度 確かめた**（足した文を含めて `HARD_REJECT` 18語 0件・`BEHAVIORAL_MARKERS` 0件）。★**IMPL への手順**=①`record_de(candidate)` のみ（**route を指定しない・`DE_ROUTE` を export しない・`ledger_path` を渡さない**）②**1件だけ。2件目を続けて入れない** ③**返り（admitted/design_evidence_id/admission_status）を BUILT にそのまま書く** ④**入れ直さない。消そうとしない**。★**呼んだ後に CC-α がやること**=`GET /api/resolve?id=DE-…` で引けるか確かめ引けたら DE 番号を書く／**`generated_by_principal` が `CLAUDE_CODE` で入っているかを front door の返りで確かめる**／**引けなければ「引けなかった」と書き入れ直さない**——**これが本件の目的であり、入れることではなく⑭が動くかを見ることである**。★確かめていないこと=**7件・42件・17件の内訳は MGR の数え直しであり CC-α は log を読めないので確かめられない**／`record_de` が実際に動くかは呼んでいない／**submit 経由で DS/RRI に何が増えるかは docstring に「DS→RRI→residual→DS thread を回す」と在るが中身は読んでいない**。*
