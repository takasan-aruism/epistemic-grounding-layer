# 科目決定を「明細成立後に共通して通る一点」へ接続した ―― 受入条件8項目

作成: Claude Code (MGR) / 2026-08-24 / ITEM: `ITEM-2DER-EVO-0100`
関連: `ART-90fe700269`(原因分解) / `ART-dd54fb656c`(親仕様)

## 0. 実装前の全件調査 ―― 接続点の根拠

**明細を立てる口 `raise_question` の本番呼び手（5repo走査・試験を除く）**:

| 呼び手 | 経路 | `_account_for` を通るか |
|---|---|---|
| `twoder/submit.py:405` | front door | ○ |
| `twoder/submit.py:619` | front door | ○ |
| `twoder/webui.py:1775` | `/api/rthread_add`（UI direct） | **×** |
| `twoder/domain_sysops.py:112` | SysOps Domain | **×** |
| `egl/structure/s_esde_evaluate.py:412` | ESDE Worker | **×** |

★**科目決定を通すのは `submit.py` だけ**。これが `PROPOSE_ACCOUNT_ABSENT` の正体。

**明細成立後に全明細が共通して通る既存の一点** ＝ **`twoder/detail_backfill.plan_backfill`**
（`RT.list_threads()` を舐める・front door / direct を問わない・W1 の planner）。
★ここへ接続した。**第二経路を手書きで増やしていない。**

## 1. 対象の条件（3つとも満たすものだけ）

| # | 条件 | 何を守るか |
|---|---|---|
| ① | いま載っている科目が `UNCLASSIFIED` / `None` | ★既に科目が在る250件に何もしない |
| ② | `QUESTION_ACCOUNT_PROPOSED` が1件も無い | ★chart外43件は提案を持つので対象外 ／ ★2回目の増分0 |
| ③ | 本文が空でない（`_ledger_records` と同じ判定） | 偽の点を作らない |

★dry_run で **対象 = 136件**、裁定の数と**完全一致**。

## 2. ★LLM の権限を迂回していない

判定ロジック（`submit._account_for` の2段）は**1バイトも変えていない**。違いは1つだけ:

```
段1  account_gate.decide          決定論 / CPUのみ / :8005 不使用   → そのまま実行
     ↓ 決まらなければ
★    authority.gate("USE_VLLM_INFERENCE")
     逐語「sending inference to the live vLLM service on :8005 (any touch of :8005)」= REQUIRES_APPROVAL
     ↓ 承認が無ければ
     ★LLM を呼ばず authority.approval_request() を返す（既存の仕組み）
段2  account_gate.decide_with_llm  ← 承認がある時だけ
```

## 3. ★★受入条件 8項目

| # | 条件 | 結果 |
|---|---|---|
| 1 | 対象136件のうち何件に proposal が新たに付いたか | **★0件**（段2に到達しないため） |
| — | （内訳）段1で科目が付いた | **★9件** |
| — | （内訳）承認待ち | **★127件** |
| 2 | 鍵B（実効的に科目が無い）が何件まで減ったか | **179 → ★170（−9）** |
| 3 | 既存科目あり群への変更 | **250 → 250（★+0）** |
| 4 | chart外43件への変更 | **43 → 43（★+0）** |
| 5 | 2回目の増分 | **proposed 0 / account_set 0**（対象数 136 → **★127**） |
| 6 | front door / direct の両経路で同じ条件 | **○**（接続点が `list_threads()` を舐めるので経路を区別しない） |
| 7 | before/after を同じ鍵Bで測る | **179 → 170** |
| 8 | Ledger Domain の台帳へ記帳 | **○**（EVO-0100） |

参考: 明細総数 1,078→1,078 ／ 割当済み 649→**658** ／ 鍵A 429→420 ／ errors **0**

## 4. ★一番大きな発見 ―― front door と後追いの非対称

**136件のうち127件（93.4%）は Taka の承認なしには動かない。**

理由は前段の設計にある:
- `submit.py` は投入時に `_account_for` を呼び、その中で**段2（:8005）が authority を通らずに走っている**
- 同じ判定を後から通そうとすると `USE_VLLM_INFERENCE`(REQUIRES_APPROVAL) に当たる

★**迂回すれば127件は今すぐ動く。しかし迂回しない**（裁定の逐語）。
★∴ ★この非対称そのものが裁定事項である。

★段1（決定論）で決まったのは **136件中9件（6.6%）** だけ。
`account_gate.decide` は逐語「採択済みの軸だけ見る」ため、**採択済み科目の少なさが段1の効きを縛っている**。

## 5. ★やっていないこと（隠さない）

- **250件に割当eventを後付けしていない**（KPIを見栄えだけ整えない）
- chart外43件に何もしていない（`admit_ledger_tree_accounts` の裁定境界を維持）
- `propose_account` の判定ロジックを変えていない
- **新台帳0 / 新state0 / 新ID族0 / 新分類語彙0**（返りの鍵は既存語のみ・試験で固定）
- 承認を自分に出していない（127件は要求を積んだだけ）
