# 実装 → 設計/監査: (a) retention 補修 — 発話記録に「直前発話」と「実時刻」が入るようになった（BUILT）

- 宛: DESIGN/AUDIT（CC-α） / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-26 / TYPE=BUILT
- 実装源: `CC_DESIGN_2026-07-26_RETENTION_REPAIR_A_BUILD_SPEC.md` v1.0（★実装源）
- 権限: `CC_MGR_2026-07-26_RETENTION_REPAIR_A_GO.md`（Taka GO）＋ **Taka から直接確認済（2026-07-26）**
- 表記規約: **【監査:IMPL】** / **【設計:IMPL】** / **【伝聞】**

## 0. 一行
**記録が入るようになりました。** ただし **P2 が実データで効くことは、まだ何も示していません。**

## 1. 変更（2点・小さい）
| repo | ファイル | 内容 |
|---|---|---|
| `ds` | `ds/phase0.py` | `last_utterance_id(conversation_id)` を新設（同一会話の直前 UTTERANCE id を決定論で返す／無ければ `None`）。`record_utterance` に `ts_source`（`CALLER`/`DEFAULT`/`UNSPECIFIED`）を追加しレコードに書く |
| `twoder` | `submit.py` | front door の呼び出しで、**既定化の前に** `ts_source` を確定し、`preceding_utterance_ref` と併せて渡す |

**新しい情報源は使っていません**（既存台帳の読み取りのみ）。**他の `record_utterance` 呼び出し経路の意味論は変えていません**（呼び出し口だけを触りました）。

## 2. 受入【監査:IMPL】
| # | 条件 | 結果 |
|---|---|---|
| **A1** | **既存 LIVE の非回帰（最優先）** | `test_preflight_gate` **13/13** / `ds/test_ds_phase0` **19/19** / `test_return_loop` **12/12** / `test_dispatch_provenance` **11/11** / `test_edge6_complete_close` **9/9** / `test_artifact_registry` **17/17** — **すべて PASS** |
| **A2** | `preceding_utterance_ref` が埋まる | 会話の先頭 = `None` / 2件目 = 先頭を指す / 3件目 = 2件目を指す / **別会話は繋がない** ✓ |
| **A3** | `ts_source` が `CALLER`/`DEFAULT` を区別 | ✓ |
| **A4** | **既存レコードの差分ゼロ** | baseline **1160行を逐語比較・変化行なし** ✓ |
| **A5** | 母数の記録 | 生 **488** → 機械生成除外 **29** → **459** → dedup → **298** |
| **A6** | `--check` GREEN（決定論再現） | ✓ |

検証スクリプト: `egl/structure/s_retention_repair_a.py`（LIVE 台帳を汚さないよう `DS_DATA_DIR` を差し替えた子プロセスで記録経路を動かします）。

### ★front door を通した実記録での確認【監査:IMPL】
本 BUILT に対応する DE 記録（`record_de` → `submit`）が実際にこうなりました:
```
utterance_id            : UTT-0739
preceding_utterance_ref : UTT-0738      ← 直前発話が入った
ts_source               : CALLER        ← 実時刻の出所が記録された
timestamp               : 2026-07-26T12:00:47Z   ← 従来のハードコード値 2026-07-11T08:00:00 ではない
```

## 3. ★言えること / 言えないこと（SPEC §5 の規律）
- **言える**: **今後の発話に直前 id と実時刻が入る。**
- **言えない**: **「P2 が実データで効く」。** それは記録が貯まってから初めて測れます。**別スライスです。**
- **前向きのみ**: 既存 **459件は復元しません**。現時点で LIVE 台帳の新フィールド充足は **0/738**（本 DE の1件を除く）で、**それが正常**です。
- **P2 ゲートへの `context` 配線はしていません**（Build 2 の scope）。**「動いた」とは書きません。**

## 4. 守った禁止事項（SPEC §3）
- 既存レコードの遡及書き換え **なし**（A4 で差分ゼロを実証）。
- **推測で埋めていません**: 同一会話に先行発話が無ければ `None`。呼び手が ts の出所を申告しなければ `UNSPECIFIED`（`CALLER`/`DEFAULT` を推測しない）。行順が近いだけの無関係な発話は入れません。
- 既存 LIVE 挙動の変更 **なし**（記録フィールドの追加のみ）。

## 5. commit
**commit 規約の変更を受領しました**: **`commit=Taka` は廃止。commit / push は MGR のみ。IMPL は commit しません。**（Taka から直接確認済）
触った repo: **`ds` / `twoder` / `egl`**。**それぞれ commit + push が必要**です（新規 structure script `s_retention_repair_a.py` は commit 同梱必須＝meta self-heal hook）。

## 6. 次
- **記録が貯まった後に、P2 の束縛先条件を実 context で測り直す**（別スライス）。**今日は1件も貯まっていないので測りません。**
- Build 2（縦串・`context` 配線）は従来どおり別。

---
*IMPL BUILT。(a) retention 補修＝記録の規律の補修であって機能追加ではない。受入 A1〜A6 すべて PASS・既存差分ゼロ・front door の実記録で直前発話 id と実時刻の記録を確認。**前向きのみ**であり、P2 が効くことは何も示していない。commit/push は MGR（規約変更を受領）。*
