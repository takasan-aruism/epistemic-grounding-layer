# 設計/監査 → MGR（写: Taka）: D-12 — **Taka の流れと現物の差分表**（設計はこの後）

- `BUILD_ROLE: 参照`（実装源ではない。**差分表のみ。設計は次段**）
- **宛: MGR** / 写: Taka / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.1）**
- **受領した MGR 文書**: `CC_MGR_2026-07-27_TAKA_FLOW_AND_LONG_INPUT_GAP.md`（D-12）/ `CC_MGR_2026-07-27_BUILD8_APPROVED.md`

## 0. 結論（先に2つ）
1. **★MGR が前提に置いた「空入力の reject は在る」は誤りである。** **本番 front door に空入力の判定は無い。** `is_empty_input()` は**研究スクリプト2本にしか存在しない**（本日4回目の「正しく作ったが作用する場所に無い」）。
2. **代わりに DS が例外で落ちる。** 空入力は**判定されて止まる**のではなく、**`ValueError` で異常終了する。**

---

## 1. 差分表（各段に LIVE / 研究 / stub / 無い を付ける）

### 1-1. DS ——「RRI に繋ぐかの判定」
| Taka の流れ | 現物 | 状態 |
|---|---|---|
| 空の投稿の検知 | **本番に無い。** `is_empty_input()` は `egl/structure/s_intent_role_split_d2p2.py` と `s_back_thin_slice_build2.py` にのみ存在 | **研究スクリプトのみ** |
| （空入力を投げるとどうなるか） | **`ds/phase0.py:101` が `ValueError("raw_text must be a non-empty string")` を送出**して落ちる | **LIVE だが「判定」ではなく「例外」** |
| 無意味投稿の検知 | 見当たらない | **無い** |
| 意味の薄い投稿の検知 | 見当たらない | **無い** |
| **「RRI に繋ぐかどうか」を決める段そのもの** | **無い。** `submit()` は DS 記録の直後、無条件に RRI へ進む | **無い** |

```
再現: grep -rln "is_empty_input" --include=*.py .
     → egl/structure/s_intent_role_split_d2p2.py / egl/structure/s_back_thin_slice_build2.py のみ
再現: python3 -c "import sys;sys.path.insert(0,'.');import twoder.submit as S;S.submit('   ')"
     → ValueError: raw_text must be a non-empty string  （1回のみ実行・断定はしない）
```
**【設計:CC-α】Taka の流れで DS に置かれている「接続するかの判定」は、現物では段として存在しない。**

### 1-2. RRI ——「4軸・7カテゴリから機械的に 2DER の機能を選別」
| Taka の流れ | 現物 | 状態 |
|---|---|---|
| 4軸・7カテゴリの分類 | `request_type.classify_request_type`（6分類）＋ `intent_strategy.resolve`（7戦略） | **両方 LIVE** |
| **そこから「2DER の機能を選別」** | **`submit.py` 段4 の ROUTING が `request_type` を見て ACQUISITION / DW / 既存 に振る** | **LIVE** |
| Build 2 の第2メニュー（`RETRIEVE`/`REGISTER`/`PREP_IMPL`/`OBSERVE`/`CONVERSE`） | `egl/structure/s_back_thin_slice_build2.py` | **研究スクリプトのみ。本番の ROUTING とは別物** |
| 必要に応じて EGL 登録 | 段1.5 の DE admission fast path | **LIVE** |
| 必要に応じて EGL 読み出し | 段3a の grounding pass（`answer_question`） | **LIVE** |

**【設計:CC-α】RRI の機能選別は LIVE で在る。** ただし **Build 2 で設計した第2メニューは本番の ROUTING と重複しており、本番側が正典である。** **研究側を本番へ持ち込む必要は無い**（作り直しになる）。

### 1-3. EGL ——「帳簿システム」
| Taka の流れ | 現物 | 状態 |
|---|---|---|
| 帳簿的な分類で EGL 内に記帳 | `egl.de_admission.admit_design_evidence`（sole writer）＋ DE 台帳 | **LIVE** |
| 勘定科目の決定 | `structure/ACCOUNT_*.jsonl`（**account chart は完成・2軸凍結命名済**） | **LIVE。★触らない** |
| **ID ごとの細かな意味分類** | **【未確認】** 現時点で、1つの DE ID の下に**複数明細**が並ぶ構造を私は確認していない | **要調査（次段）** |

**【設計:CC-α】§1-3 の3行目が、まさに Taka が「まだ具体的になっていない」と名指しした場所である。** **本差分表では「未確認」とし、次段で現物を読む。**

### 1-4. DW（概要でよい・MGR 指示）
`dw.workcell`（`create_task` / `record_plan` / `derive_state` / `_read_events`）が **LIVE**。段4 の ROUTING から `create_task` で入る。**直叩き 18箇所のうち LIVE は 18、書きは3箇所**（既報・閉塞対象）。

---

## 2. ★長文の扱い — 3つの問いへの現状回答（事実のみ・設計は次段）
| MGR の問い | 現状の事実 |
|---|---|
| **① どこで明細に分かれるのか** | **どこでも分かれていない。** `submit()` は `raw_input` を1本の文字列として受け、1つの `request_type` と1つの `INTENT_STRATEGY` を返す。**分解する段は存在しない** |
| **② RRI は ID 単位で何を決めるのか** | **ID 単位で1つ決めている**（`request_type` 1つ・`INTENT_STRATEGY` 1つ・`DW_TASK_ID` 最大1つ） |
| **③ 分解を誰がやるのか** | **誰もやっていない**（分解が存在しないため） |

**∴ Taka の指摘「長文を1つの軸とカテゴリで扱うのはナンセンス」は、現物がまさにその状態である。**

---

## 3. ★機能追加の候補（差分表の穴から。思いつきで足さない・MGR §5-3）
**穴として確定したもの（優先順は付けない・裁定は MGR）:**
| # | 穴 | 根拠 |
|---|---|---|
| **G1** | **DS に「RRI へ繋ぐかの判定」段が無い**（空入力は例外で落ちる） | §1-1・実測 |
| **G2** | **無意味投稿・意味の薄い投稿の機械的検知が無い** | §1-1 |
| **G3** | **1つの ID の下に複数明細が並ぶ構造が未確認** | §1-3 |
| **G4** | **長文を明細に分解する段が無い** | §2 |

**【設計:CC-α】G1 は最も小さく、既に部品がある**（`is_empty_input()` が研究スクリプトに在る。**移すだけで作り直しではない**）。**ただし着手はしない。裁定を待つ。**

---

## 4. 私の誤り・保留（消さない）
- **MGR の「空入力の reject は在る」を私は今日まで訂正していなかった。** 私自身、Build 4 の SPEC で「空入力は入口で機械的に弾く」と書き、**それが研究スクリプトに実装されたことを確認して、本番に入ったと扱っていた。** **確かめていなかった。**
- **1-3 の「ID ごとの意味分類」は未確認のまま。** 次段で読む。
- **空入力の実測は1回のみ**（運用方針 §4-13）。**「常に ValueError になる」とは書かない。**

---
*CC-α D-12 差分表。★MGR 前提「空入力の reject は在る」は誤り——本番に判定は無く、DS が ValueError で落ちる（is_empty_input は研究スクリプト2本のみ＝本日4回目の「作ったが作用する場所に無い」）。DS の「接続判定」段は存在しない。RRI の機能選別は LIVE（Build 2 の第2メニューは研究のみで本番 ROUTING と重複・本番が正典）。EGL の記帳と勘定科目は LIVE（account chart は触らない）、★「ID ごとの細かな意味分類」は未確認＝Taka が名指しした未具体はここ。長文は「どこでも分かれていない・ID 単位で1つ決めている・分解は誰もやっていない」。穴は G1〜G4。着手せず裁定を待つ。*
