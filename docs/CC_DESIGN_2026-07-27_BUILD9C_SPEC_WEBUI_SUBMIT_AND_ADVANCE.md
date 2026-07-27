# BUILD SPEC — Build 9C: **webui から投入し、RUN NEXT で1段だけ進める（Qwen planner が我々の依頼を PLAN できるか）**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源。**IMPL はこの1本だけから作る**）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.5）**
- 権限: `CC_MGR_2026-07-27_D16_RULING_USE_WEBUI_PATH.md`（webui 経路を使う／CLI に進行機能を足さない／run-gate を回避しない）
- 経緯: `CC_DESIGN_2026-07-27_BUILD9B_AUDIT_AND_D16_ANSWER.md`

---

## 0. ★MGR §4 の先決事項に答えた — **認証は手元で足りる。Taka の資源は要らない**【監査:CC-α】
```
再現: stat -c '%n %U:%G %a %s' twoder/.access_token
     → twoder/.access_token  takasan:takasan  600  36 bytes     （★中身は出さない）
再現: ss -ltn | grep 8770
     → LISTEN 0 5 100.107.6.119:8770                            （webui は待ち受け中）
コード: webui.py:43-59  HTTP Basic Auth / AUTH_USER="taka" / パスワード = .access_token の中身
```
**∴ 新しい credential の発行は不要。** **MGR から Taka に諮る必要は無い。**

### 0-1. ★トークンの扱い（守ること）
- **トークンを文書・報告・ログに書かない。** **BUILT にも書かない。**
- **コマンドライン引数に置かない**（`ps` から見える）。**§2 の方法で、ファイルから読んで直接使う。**
- **コピーを作らない。**

## 0-2. これは何か
| | |
|---|---|
| **これは** | **webui から同じ依頼を投入し、`RUN NEXT` を1回だけ押して、`PLAN` が誰の手で書かれるかを観測する** |
| **これではない** | **完走させる build ではない。** 1段だけ。worker まで走らせない |
| **測るもの** | **★Qwen `BUILD_PLANNER` が、我々の依頼を PLAN できるか。** 本日ずっと測れていなかったもの |
| **境界への寄与** | **寄与する。** 「引き金は我々、仕事は Qwen」がどこまで本当かを確かめる |

---

## 1. ★段0（先に・1回だけ）— 私の推論を実測で確かめる
**私は「CLI で作った task は webui の RUN NEXT からも拒否される」と書いたが、実行していない**（`【未確認】`）。**MGR §3-5 の指示により、1回の実測で確かめる。**

```
POST /api/run_next   body: {"task_id": "TASK-2DER-D6A93450"}      ← Build 9B で CLI が作った task
```
- **`webui.py:571` の run-gate は、拒否時に dispatch も state 変更も行わない**（コード逐語: *"No dispatch, no state change."*）。**∴ 安全に確かめられる。**
- **返ってきた JSON を逐語で記録する**（`refused` / `reason` / `runnable` / `task_id`）。
- **★拒否されなかった場合は、そこで止めて設計へ上げること。** 私の読みが誤っていたことになる。**そのまま進めない。**

---

## 2. 段1 — webui から投入する（1回だけ）

**依頼文は Build 9B と同一。1文字も変えない**（`CC_DESIGN_2026-07-27_BUILD9B_SPEC_SANDBOX_ADAPTER_REQUEST.md` §1 の逐語）。
**★同じ依頼文を使う理由**: **投入口だけを変えた対照にするため。** 文面を変えると、何が効いたのか分からなくなる。

**方法（トークンを argv に置かない）:**
```python
import json, base64, urllib.request, pathlib
tok = pathlib.Path("/home/takasan/twoder/.access_token").read_text().strip()
authz = "Basic " + base64.b64encode(("taka:" + tok).encode()).decode()
def post(path, payload):
    req = urllib.request.Request("http://100.107.6.119:8770" + path,
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": authz},
                                 method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=300).read())
# 段1: post("/api/submit", {"raw": "<Build 9B §1 の依頼文>"})
# 段2: post("/api/run_next", {"task_id": <段1 で返った DW_TASK_ID>})
```
- **投入は1回だけ。** 再投入しない。**するなら「再投入した」と書く。**
- **`raw` のキー名は `webui.py:536` に合わせる**（`b.get("raw","")`）。**確認してから使うこと。**

---

## 3. 段2 — `RUN NEXT` を1回だけ
```
POST /api/run_next   body: {"task_id": <段1 の DW_TASK_ID>}
```
- **`/api/run_until_barrier` を使わない。** **1段だけ。**
- **run-gate を回避しない**（MGR 裁定3）。**拒否されたら拒否されたと記録して止める。**
- **`AUTH.gate("DW_MACHINE_DISPATCH")` で拒否された場合も、止めて記録する。**

---

## 4. ★予想を先に書く（実測前に固定・後から変えない）
| # | 項目 | DESIGN の予想 |
|---|---|---|
| 段0 | CLI task への RUN NEXT | **`refused: true`**（`tid != gate["task_id"]`） |
| 段1 | `request_type` | **`BUILD_CAPABILITY`**（Build 9B と同じ依頼文なので） |
| 段1 | `DW_TASK_ID` | **返る**（Build 9B と別の新しい task) |
| 段1 | run-gate | **`runnable: true` になる** |
| 段2 | `AUTH.gate("DW_MACHINE_DISPATCH")` | **`auto: true`**（コード逐語 *"AUTO_EXECUTE (compute, no live-service mutation). The operator does not ask Taka for this."*） |
| 段2 | `PT.plannable(task_id)` | **False**（我々の依頼は bounded reproduction candidate ではない） |
| **段2** | **★`auto_served`** | **★`QWEN_BUILD_PLANNER`（＝Qwen が PLAN を書いて記録する）に賭ける** |
| 段2 | `derive_state` | **`PLANNED` 相当**（`has_plan: True`） |

**★最後の2つが本 build の核である。**
**賭けの根拠**: **`build_planner` は過去に live で planner→worker→test→judge まで到達したと記録に在る。** **【未確認】——私はその記録を確かめていない。** **∴ 根拠の弱い賭けである。外れても不思議はない。**
**外れ方は2つある。両者を区別して書くこと:**
- **(a) planner が走ったが `validate_plan` が拒否した** → **`reasons` を逐語で記録する。★これが最も価値のある観測である**（何が足りないかが名指しで出る）
- **(b) planner がそもそも呼ばれず Claude barrier に落ちた** → `auto_served` が無く `claude_barrier: true`

---

## 5. やってはいけないこと
1. **PLAN を手で書かない。** planner が拒否したら、そこで止める。**補完しない。**
2. **2段以上進めない。** worker を走らせない。
3. **run-gate / authority gate を回避しない。** 環境変数や直接呼び出しで迂回しない。
4. **依頼文を書き換えない。**
5. **トークンを記録に残さない**（§0-1）。
6. **本番コードを変更しない。** 必要になったら止めて設計へ上げる。
7. **`twoder/operator.py` を改名しない。**

---

## 6. 受入
1. **段0 の返り値を逐語で記録**（`refused` / `reason` / `runnable` / `task_id`）。
2. **段1 の `TRACE` 全項目**（`RRI_REQUEST_TYPE` / `RRI_PREFLIGHT` / `INTENT_STRATEGY` / `SELECTED_ACQUISITION_METHOD` / `DISPATCH_RESULT` / `DW_TASK_ID`）。
3. **段2 の返り値を逐語で記録**（`dispatched` / `reason` / `nlo` / `auto_served` があれば それも）。
4. **`derive_state(<新 task>)` の結果**（`has_plan` を含む）。
5. **★`auto_served` の値を名指しで書く。** 無ければ「無い」と書く。
6. **★拒否された場合、`reasons` / `reject_reason` を逐語で全部書く。** 要約しない。
7. **PLAN が記録された場合、その `implementation_packet` の `target_workspace` と `files_expected` を書く。** **中身の良し悪しは判定しない。**
8. **sandbox が作られたか**（`/tmp/2der_runner_*` の増減を投入前後で数える）。**作られていても、成果物には触らない**（本 build は PLAN までのため）。
9. **§4 の予想と実際の表。外れた項目に「外れた」と書く。**
10. **本番コードが変わっていないこと。**
11. **1回しか投入していないこと・1段しか進めていないことを明記。**
12. **★front door を経て設計/監査に「届いた」のか、自分で読みに行っただけなのかを1行で書く**（Build 8/9B で2回続けて欠落）。
13. **観測を書き、判定・評価・提案をしない。** 判定は設計/監査。
14. **commit しない。**
15. **BUILT 冒頭に「運用方針 確認済（版: v1.5）」と受領文書一覧。**
16. **v1.5**: 「動く」と書くときは実行した再現コマンドと結果を併記する。

---

## 7. 併せて（別作業・小さい）
**`twoder/ledger_query.py` を削除すること。**
- **根拠**【監査:CC-α】: `.py` からの import 0件・設定からの参照 0件（`grep -rn "ledger_query" --include=*.py --include=*.json .`）。未追跡ファイル。
- **理由を BUILT に記録する**: SUPERSEDED／`twoder/ids.py::resolve` と重複／**2本目の読み口は境界にとって最悪（どちらが正典か決まらない）**。
- **他のファイルを消さないこと。**

---

## 8. 位置づけ（緩めない）
- **PLAN が Qwen で書かれても「Claude を使わない開発体制になった」と書かない。** **引き金を引いたのは我々である。**
- **本 build が示せるのは「webui 経路なら1段進むか」と「PLAN を誰が書いたか」だけである。**
- **1回の観測で planner の可否を断定しない**（v1.5 §4-13）。

---
*BUILD SPEC v1.0（★実装源）。Build 9C=webui `/api/submit` から Build 9B と同一の依頼文を投入し、`RUN NEXT` を1回だけ押して PLAN を誰が書くかを観測する。★MGR の先決事項に回答: 認証は手元で足りる（`.access_token` は takasan 所有 600・webui は 100.107.6.119:8770 で待ち受け中）＝Taka の資源は不要。トークンは文書・argv・ログに出さない（python で直接読む方法を指定）。★段0=私の未確認の推論「CLI の task は webui からも拒否される」を1回の実測で確かめる（拒否時は dispatch も state 変更も無いので安全。拒否されなかったら止めて上げる）。段1=同一依頼文で投入（投入口だけを変えた対照にするため文面を変えない）。段2=`run_next` 1回のみ、`run_until_barrier` を使わず run-gate も authority gate も回避しない。★予想を固定——段0 refused / BUILD_CAPABILITY / runnable=true / DW_MACHINE_DISPATCH は auto / `PT.plannable` は False / **★`auto_served=QWEN_BUILD_PLANNER` に賭ける**（根拠は過去の live 実証の記録だが私は未確認＝根拠の弱い賭け）。外れ方は (a) planner が走って validate_plan が拒否（`reasons` 逐語が最も価値ある観測）と (b) planner が呼ばれず Claude barrier、を区別して書く。禁止=PLAN を手で書かない・2段以上進めない・gate を迂回しない・依頼文を変えない・トークンを残さない・本番無変更。併せて `ledger_query.py` を削除（参照0件を確認済・理由を記録）。PLAN が Qwen で書かれても「Claude を使わない体制になった」と書かない——引き金を引いたのは我々。*
