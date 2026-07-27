# 実装 → 設計/監査: Build 9B — 投入した。**task は作られたが planner に到達せず、成果物は生成されていない**（BUILT）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=BUILT
- **運用方針 確認済（版: v1.5）**
- 実装源: `CC_DESIGN_2026-07-27_BUILD9B_SPEC_SANDBOX_ADAPTER_REQUEST.md` v1.0
- **受領した文書**: 上記実装源 / `CC_DESIGN_..._BUILD9A_STOP_PLANNER_REJECTS_PROD_REPO.md`（STOP）/ `CC_MGR_2026-07-27_BUILD9B_APPROVED.md`（写しで観測）
- **本文書は観測を書きます。判定・評価・提案をしません。**

## 0. 着手前に読みました（実装源 §0）【監査:IMPL】
- `twoder/ids.py`（**88行**。`resolve(rid, ledger_path=None)` が `UTT-` / `DEV-` / `THREAD-` 等を接頭辞分岐で解決）
- `twoder/build_planner.py`：`STRUCTURED_KEYS`（35行〜・`target_workspace` は "NOT a production repo" と明記）/ `PROD_REPO_ROOTS`（59行〜・**`/home/takasan/twoder` を含む**）/ `DESTRUCTIVE_MARKERS`（55行〜）
- `twoder/artifact_registry.py` docstring（**「パスと散文は信用しない。artifact record を使う」**）

## 1. 投入（1回のみ）【監査:IMPL】
```
cd /home/takasan && python3 -m twoder.submit "<実装源 §1 の依頼文>"   → exit=0
```
**依頼文は1文字も変えていません。再投入していません。** 台帳 **1180 → 1181**（1行）。

## 2. ★予想と実際（実装源 §3）
| 項目 | DESIGN の予想 | **実際** | 判定 |
|---|---|---|---|
| `RRI_REQUEST_TYPE.request_type` | `BUILD_CAPABILITY` | **`BUILD_CAPABILITY`** | **当たり** |
| `RRI_PREFLIGHT.triggered` | `False` | **`False`**（`ALLOW`） | **当たり** |
| `INTENT_STRATEGY.strategy` | `DIRECT` | **`null` / `status=NO_CANDIDATE`** | **★外れ** |
| `DW_TASK_ID` | 返る | **`TASK-2DER-D6A93450`** | **当たり** |
| `build_planner.validate_plan` | 通る | **★到達していない**（下記 §3） | **判定不能** |

## 3. 返ってきた `TRACE`（全項目）
```
RRI_REQUEST_TYPE            : BUILD_CAPABILITY / requires_current_state=false / references_prior_work=false
RRI_PREFLIGHT               : triggered=false / decision=ALLOW
INTENT_STRATEGY             : strategy=null / candidates=[] / status=NO_CANDIDATE /
                              facts_emitted=false / fact_trace=["SELF_CONTAINED_NO_FACTS"]
SELECTED_ACQUISITION_METHOD : DW_IMPLEMENTATION
DW_TASK_ID                  : TASK-2DER-D6A93450
ACTOR_ROLE                  : MANAGER
DISPATCH_RESULT             : PENDING (loop-owned): actor=CLAUDE input=GOAL+KNOWLEDGE_PACKET
NEXT_LEGAL_OPERATION        : PLAN
```
`TRACE` 全文は `scratchpad/b9b.json` に保存しています。

## 4. ★task の進行（実装源 §2 ③）【監査:IMPL】
```
derive_state('TASK-2DER-D6A93450') = ('CREATED', {'has_plan': False, 'generate_runs': [],
                                       'audit_runs': [], 'upper_reviews': [], 'rework_count': 0, …})
event 数 = 1   （phase=CREATE / actor=None）
```
**＝ task は作られましたが、`CREATE` の1イベントのみで `PLAN` に到達していません。**
`DISPATCH_RESULT` は `PENDING (loop-owned): actor=CLAUDE` で、**`submit()` の呼出内では planner / worker は起動していません。**

## 5. ★成果物の受け取り（実装源 §2 ④・§2-2）【監査:IMPL】
```
投入前の /tmp/2der_runner_* : 56 ディレクトリ
投入後の /tmp/2der_runner_* : 56 ディレクトリ（増減なし）
find /tmp -maxdepth 1 -name "2der_runner_*" -newermt "-10 minutes" → 0 件
```
**＝ 新しい sandbox ディレクトリは作られていません。生成された成果物はありません。**
**保全（`dev-workcell/contracts/out/SANDBOX_ARTIFACT-<TASK_ID>/`）は行っていません**——**保全する対象が存在しないためです。** `MANIFEST.json` も作っていません。

**「失われた」のではありません。** **そもそも生成が起きていません**（§4 のとおり `PLAN` 未到達）。

## 6. ★失敗の書き分け（実装源 §3）【監査:IMPL・観測の限界を含む】
実装源が用意した4区分は次のとおりです:
```
(1) 作れなかった   planner/worker がコードを出せなかった／依頼と無関係なものを出した
(2) 作れたが置けなかった
(3) 置けたが動かなかった
(4) 通った
```
**観測された状態は、この4つのいずれにも正確には当てはまりません。**
- **(1) は「planner/worker が動いた上で出せなかった」ことを前提としています。** 今回は **`CREATE` の1イベントのみで planner が起動していません。**
- ＝ **観測されたのは「生成の限界」より手前の状態**です。**これ以上の区分は、私の観測だけでは判定材料が不足しています。**

**私は区分を新設していません。判定は設計/監査にお願いします。**

## 7. 守った禁止事項（実装源 §4・確認）
- **手で配線を書いていません。worker が出せなかった部分を補完していません。**
- **手で配置していません**（配置対象が存在しません）。
- **依頼文を書き換えて再投入していません**（投入は1回）。
- **`twoder/operator.py` を改名していません。**
- **`ids.resolve()` の正しさを台帳と照合していません。**
- **本番コードを変更していません**（`submit.py` を含め1行も）。

## 8. ★未処理として申告します（本 build の対象外）
**`twoder/ledger_query.py`（6,931 bytes・未追跡 `??`・未 commit・未実行）が存在します。**
Build 9 の実装源が差し戻される前に私が書いたもので、**その後 SUPERSEDED になり、既存 `twoder/ids.py::resolve` と重なることが指摘されています。**
**本 build では触っていません。扱いの指示を待ちます。**

## 9. commit
**していません**（MGR）。

---
*IMPL BUILT（Build 9B）。着手前に3ファイルを実読。依頼文を1文字も変えず1回だけ投入（台帳1180→1181）。**予想は4項目中3項目が当たり、`INTENT_STRATEGY` は `DIRECT` の予想に対し `NO_CANDIDATE` で外れた。** `DW_TASK_ID=TASK-2DER-D6A93450` は返ったが **`CREATE` の1イベントのみで `PLAN` 未到達**、`DISPATCH_RESULT=PENDING (loop-owned): actor=CLAUDE`。**新しい sandbox ディレクトリは作られておらず（56→56）、成果物は存在しない**ため保全していない。**実装源の4区分のいずれにも正確には当てはまらない**（(1) は planner 起動を前提とするため）——区分は新設せず判定は設計/監査へ。本番コード無変更。*
