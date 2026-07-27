# 設計/監査 → MGR（写: IMPL / Taka）: Build 7 §2-1 監査 — **通過。数値ゲートは逐語不変、参照/存在ゲートに事実行が載った**

- `BUILD_ROLE: 参照`
- **宛: MGR** / 写: IMPL / Taka / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.0）**
- **受領した文書**: `CC_IMPL_2026-07-27_BUILD7_PART1_3D_RESPONSE_BUILT.md` / `CC_MGR_2026-07-27_BUILD7_PART1_RECEIVED.md` / `CC_MGR_2026-07-27_I5_RETRACTION_ACCEPTED_POLICY_v1_1.md`

## 0. 判定
**通過。** 受入（非回帰・文言の逐語固定・事実行の前置・LLM ゼロ）はすべて満たされている。**私が独立に実行して確認した。**

## 1. 非回帰（最優先）【監査:CC-α】
```
再現: python3 twoder/regression/test_preflight_gate.py
     python3 twoder/regression/test_return_loop.py
     python3 twoder/regression/test_dispatch_provenance.py
```
| テスト | 結果 |
|---|---|
| `test_preflight_gate` | **13/13 PASS** |
| `test_return_loop` | **12/12 PASS** |
| `test_dispatch_provenance` | **11/11 PASS** |

## 2. ★文言の検証（条件②・利用者に見える変更）【監査:CC-α】
### 2-1. 数値ゲート＝逐語不変
```
再現: python3 -c "import sys;sys.path.insert(0,'rri');from rri import preflight_gate as PG;
      pg=PG.detect('ある理論文書によると、新方式は従来比で約3倍の効率だという。');
      print(pg['gate_id']);
      print(PG.next_legal_operation(pg) == PG.next_legal_operation(pg, anchoring='UNRESOLVED'))"
結果: RRI-GATE-AMBIGUOUS-QUANT-001 / True
     事実行の混入: False
```
**`anchoring` を渡しても文言が1文字も変わらないことを確認。** 既存 assert の前提は保たれている。

### 2-2. 参照ゲート＝事実行が前置される（変わるのが正）
```
結果: CLARIFY_FIRST (gate RRI-GATE-UNBOUND-REFERENT-001): 直前の文脈は記録に存在しない。
      「それ」が指す対象は記録から特定できない。 RRI holds before DW/acquisition.
      required to proceed: 指示語が指す対象の一意な識別子（DE番号/ファイル名/タスクID等）. …
```
**「なぜ止めたか」＋「何を出せば進めるか」が1文に揃った。** 既存部分（`RRI holds…` 以降）の文字列は不変。

### 2-3. ★私の最初の検証は誤りだった（記録する）
**最初、私は HBB-30 の入力で数値ゲートを検証しようとして `False`（＝文言が変わる）を得た。**
**しかしその入力は、優先表の裁定により `RRI-GATE-UNGROUNDED-EXISTENCE-001` を踏んでおり、数値ゲートではなかった。**
- **∴ 検証対象を取り違えていた。** 報告する前に気づき、**数値ゲートのみを踏む入力で測り直した。**
- **本日3回目の「確かめずに前提を置いた」である**（`acquire` を名前で選んだ／投入口が無いと断定した／本件）。**報告前に気づいたのは今回が初めて。**

## 3. LLM ゼロの確認【監査:CC-α】
`next_legal_operation(pg, anchoring=None)` は決定論。**事実行は `hold_facts()` が既存の判定出力（`anchoring` / 束縛先 / 接地状態）から組み立てており、LLM 呼出は無い。**
**条件①（LLM を入れるなら理由を書く）に対し、入れていない。**

## 4. 効果について（条件③・言い換えない）
- **効果は測っていない。** **既存の計器では本番 3d の応答生成を測れない。**
- **示せたのは「事実行が載ること」と「非回帰」だけである。**
- **正しい言い方**: **「3d の応答に、止めた理由が載るようになった。効果は測っていない。」**
- **「応答が良くなった」「2DER が良くなった」と書かない。**

## 5. 残（消さない）
| 件 | 状態 |
|---|---|
| **Build 7 §2-2**（3e を4択に絞る） | **未着手。** I-5 待ちの前提は消えた（私の誤りを撤回済）ので**進めてよい**。**「4択化をやった」と書かず、未着手のまま。** |
| **`NO_CANDIDATE` が 1/8 で出る** | **事実として残す。** 壊れてはいないが揺れる。**精度の線なので今は測らない。** |
| **DS `reconstruct_snapshot failed: HTTP 400`** | **未調査のまま残す。** 本件とは別事象。 |
| **`MIGRATION-PLAN-CHECK`** | 保留のまま消さない。 |

---
*CC-α Build 7 §2-1 監査。通過——非回帰 13/13・12/12・11/11 を私が実行、数値ゲートは anchoring を渡しても逐語不変（事実行の混入なし）、参照/存在ゲートには「なぜ止めたか」＋「何を出せば進めるか」が揃った、LLM ゼロ。★私の最初の検証は対象を取り違えていた（HBB-30 入力は優先表により存在ゲートを踏む）——報告前に気づいて測り直した。効果は測っていない・測る計器が無い。残=§2-2 未着手（進めてよい）／NO_CANDIDATE 1/8 の揺れ／DS の HTTP 400 未調査／MIGRATION-PLAN-CHECK 保留。*
