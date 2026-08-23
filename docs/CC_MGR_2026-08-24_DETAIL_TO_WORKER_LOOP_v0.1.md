# ①② 明細→worker の辺を通し、1本のTASKで循環を完走した v0.1

**作成: Claude Code（MGR）／ 2026-08-24**
**裁定（逐語）: ① 明細→workerの辺を通す ② 1本のTASKで「明細→PLAN/DW→結果→明細」の循環を完走
③ その後、既存990件への適用拡大 ④ 最後に類似TASK統合・テンプレート学習**
**前提: 現状対応表（`ART-576edd4ee2`）§6 の優先1「明細 → 処理」と優先2「処理 → 明細」**

---

## 0. 実装前の全件調査 — ★既存の面が2つ見つかった

| 調べたこと | 実測 |
|---|---|
| worker/planner に届く入力面 | `_plan_prompt(goal, provenance)` の2つだけ。goal＝依頼文の逐語、provenance＝`_observation_facts` が組む事実 block |
| `_observation_facts` の作法（逐語） | 「既に取得済みの観測を、★事実として planner に見せる（★指示は足さない。事実だけ渡す）」「解決できない参照は黙って落とす（fail-closed）」「渡せるものが1つも無ければ空文字＝従来と同じ prompt」 |
| CREATE payload | `goal` / `knowledge_packet` / `project_id` / `supersedes`。**`knowledge_packet` に既に `open_gaps` / `admitted_claims` / `source_trace` がある** |
| KP の読み手 | `dw/plan_template.create_knowledge_packet` → `dw/dispatch.py:131` |
| provenance | `dw_task_id` / `egl_open_gaps` / `egl_source_refs` ほか。**`rthread_id` は無い** |
| TRACE の読み手 | `webui._trace` と `ids.py` の2箇所だけ（`runs/{task_id}.trace.json`） |
| 戻りの辺（結果→明細） | **0件**。`twoder/gap_report.py` も逐語で「★record_evidence / list_evidence は在る。★調査で得た証拠が明細に戻っていない」と報告している |

∴ **新しい面を作る必要はなかった。** `_observation_facts` と同じ位置・同じ作法で事実 block を1つ足すだけで足りる。

---

## 1. ① 明細 → worker（`build_planner._detail_facts`）

### 1.1 ★原文を二度渡さない

`goal` は既に逐語で渡っている。∴ **明細の `source_text` を足すのは重複でしかない。**
渡すのは**原文からは出てこないものだけ**:

| # | 渡すもの | なぜ原文から出ないか |
|---|---|---|
| 1 | 依頼の形の不足（`REQUEST_GAPS`） | **機械が数えた不在**。書かれていないものは読めない |
| 2 | 明細が指す先で実在しなかったもの | **IO で確かめた結果**（repo に対する実在確認） |
| 3 | 既に確かめられたもの | **根拠の id と種類**（`basis_kind`/`validation_mode`/`ART-`/`ETR-`） |
| 4 | まだ決着していない明細の数 | **台帳の現在状態** |

②は `FACT`/`TEST`/`CONSTRAINT` のみを穴として扱う（`SPEC`/`CHANGE`/`GOAL` が指す先が無いのは
これから作る物＝正常。段2 の `KINDS_MUST_EXIST` と同じ規律）。

**根拠となった実測（2026-08-23）**: 同じ内容を書き直した2本の対照 ――
`EF6826DC`（SPEC 0 / TEST 0）は **worker が依頼文に無い挙動を発明して2周失敗し打ち切り**、
`ED65242E`（SPEC 8 / TEST 6）は成立。**不足は投入時に決定論で取れる信号である。**

### 1.2 ★従来の prompt を1バイトも変えていない（実測）

```
task_id 無し           → 従来と同一（2,536バイト）  ★True
明細が無い task        → 従来と同一               ★True
引けない/例外          → 空文字を返す（planner を止めない）
明細が在る task        → +554バイト
```

封印試験 `test_prompt_is_byte_identical_when_no_task_id` /
`test_prompt_is_byte_identical_for_a_task_with_no_details` /
`test_detail_facts_never_raises` で固定した。

---

## 2. ② 戻りの辺（`twoder/detail_feedback.py`）

**新 event type 0 / 新 ID 体系 0 / 新台帳 0 / 新 state 0。**
段4 の `rri.request_thread.record_evidence` をそのまま呼び、根拠の id は既に在る `ETR-`（実行の痕跡）を指す。

書く内容は**観測した事実だけ**:
`basis_kind=LOCAL_MEASUREMENT` / `validation_mode=MEASURED` /
`evidence_refs=[その走行の ETRACE event id]` / `evidence_text=合否と落ちた試験名`。

**★粒度は「依頼」**（`question_id=None`）。段4 の記録（`ART-e5d4dfbe65` §5）で確定したとおり、
**どの明細の試験かを決定論で引く鍵が無い**（封印試験は依頼文より後に生成され、
どの明細から出た試験かを記録していない）∴ **推測で明細へ結ばない。**
封印試験 `test_feed_back_grain_is_the_request_not_a_guessed_detail` で固定した。

---

## 3. ★循環を1本のTASKで完走した（ED65242E・本番の台帳）

```
[1] 明細 → PLAN        prompt に 554バイトの事実が届いた
                       - Q-9d3f4bb0: verified as LOCAL_CODE_OBSERVATION/OBSERVED from ART-630e5f23cb
                       - Q-19be9e79: verified as LOCAL_CODE_OBSERVATION/OBSERVED from ART-ae789b58f7
                       - UNSETTLED ITEMS: 25 of 27
[2] PLAN/DW → 結果     ETR-44dcd91f1c71-0009  run_minimal_slice  FAILED
[3] 結果 → 明細        QE-f764b760 を記帳（根拠 3件 → 4件）
                       "run_minimal_slice FAILED / status=FAILED"
[4] ★循環が閉じた      次の PLAN の事実が 554 → 641バイト（★+87）
                       ★- (request level): verified as LOCAL_MEASUREMENT/MEASURED
                            from ETR-44dcd91f1c71-0009
[5] ★保存則            I1/I2 例外なし  status=NARROWING raised=27 resolved=2 in_flight=25
                       ★QUESTION_RAISED 無改変（per_account_balances = {UNCLASSIFIED: 27}）
[6] ★冪等              同じ走行を2回入れても evidence_id は同じ・件数は4件のまま
```

**`[3] で書いたものが `[4] で PLAN に返ってくる** ―― これが循環が閉じた証拠である。

---

## 4. ★自分の誤りを2つ直した

1. **ヒアドキュメントの `\n` が実体化して `build_planner.py` を壊した**。git から戻し、
   raw 文字列で書き直した（**壊れたまま進めていない**）。
2. **封印試験の前提が強すぎた**。`test_build_planner` が走行台帳を差し替えると痕跡が引けなくなり、
   `dry_run` の理由文が別のものになる。**どちらの場合でも変わらないのは「1バイトも書いていない」こと**
   ∴ そこだけを締めるよう緩めた。順序を3通り変えて全通過を確認。

---

## 5. 触っていないもの

- `dev-workcell` 全体（**1バイトも触っていない**）／ `webui.py`（担当が別インスタンス）
- `_observation_facts` / `validate_plan` / `dispatch_provenance`（provenance の schema は
  fail-closed で検査されているため**足していない**）
- `knowledge_packet` の組み立て（EGL の管轄）
- 既存 990明細のうち ED65242E の27件以外（**1件も触っていない**）
- `EVENT_TYPES` / `DISPOSALS` / `STATES` / `TRANSITIONS`

---

## 6. ★まだ通っていないもの（正直に）

1. **戻りの辺に自動の呼び手が無い。** `detail_feedback.feed_back` は**手で呼んだ**。
   `manager_v0.receive_finished` → `domain_dw` に繋ぐのが自然だが、**未配線**。
   ∴ 現状は「経路は在るが、機械が自分で回してはいない」。
2. **`REQUEST_GAPS` が ED65242E の TRACE に無い**（段3 より前の投入のため）。
   ∴ (1) の block は**今回の実走では出ていない**。新規投入でしか出ない。
3. **PLAN を実際に走らせて、事実が結果を変えたかは測っていない。** 今回確認したのは
   「prompt に届いた」ことまでで、**それで worker の出力が良くなったかの対照実験はしていない**。
4. ③（既存990件への拡大）と④（類似TASK統合・テンプレート学習）は**未着手**。

## 7. 試験

`twoder` 80本（1 skip）＋ `rri` 70本 ＝ **150本 全通過**（新規11本）。
順序を変えても同じ結果になることを確認済み。
