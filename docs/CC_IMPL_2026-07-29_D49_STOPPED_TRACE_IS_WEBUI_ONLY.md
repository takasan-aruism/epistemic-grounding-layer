# 実装 → 設計/監査: **止まってよい場所①に当たりました — `etrace_run_id` は CLI 投入では `/api/state` に出ません**（原因は決定論で確定）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-29 / TYPE=BUILT（**受入1〜3・6 の未達を含む報告**）
- **運用方針 確認済（版: v2.8）**
- 実装源: `CC_DESIGN_2026-07-29_D49_UI_TWO_ITEMS_BUILD_SPEC_v1_0.md` v1.0 §6-1（**「`etrace_run_id` を足しても `/api/state` に出ない → ★私の見立てが外れた。報告する」**）
- 権限: `CC_MGR_2026-07-29_D49_SUBMIT_TEXT_APPROVED.md`（承認文面・1回だけ）

## 到達経路
- [x] **(A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**

## 結果（★2軸）
### 経路
- [x] **実装した**（`build_state` に2キー／`/command` にカード2枚）
- [x] **★受入1〜3 の手前で止めた**（実装源 §6-1 に該当）
### 実測
- [x] **受入4 既存キーが不変**（sha256 `d6d888bea8334bd0` が前後一致・消えたキー0）
- [x] **受入5 非回帰 91 passed / 7 failed**（基準と顔ぶれ diff 空）
- [ ] **受入1・2・3 ★未達**（§2 の理由）
- [x] **受入6 ★満たした**（`etrace_run_id` が無くても画面が壊れない。**皮肉にも今回の task がその実例です**）

---

## 1. 投入（承認文面のまま・1回だけ）
```
再現: cd /home/takasan && python3 -m twoder.submit "<承認文面・1文字も変えず>"
  exit=0
  ★DW_TASK_ID       = TASK-2DER-AC13F06E     ← ★DW task は作られた
  RRI_REQUEST_TYPE  = BUILD_CAPABILITY       ← ★狙いどおり routing された
  ETRACE_RUN_ID     = ETR-88bc41400d19       ← ★submit の返りには在る
```
**★MGR 条件1（`BUILD_CAPABILITY` にならなければ止める）には当たりません。** **なりました。**
**★webui は投入前に再起動しています**（新 pid `3410734` / 01:15:55 起動）。

## 2. ★止まった理由（決定論・私の見立てが外れました）
```
再現: GET /api/state?task_id=TASK-2DER-AC13F06E
  ① DW task        : TASK-2DER-AC13F06E / dw_state = CREATED
  ② 捉えた問い     : ★None
  ④ 次の操作       : PLAN → CLAUDE / PENDING EXTERNAL ACTOR
  ⑥ Taka 判断      : []
  ★③ etrace_run_id     : ★None
  ★⑤ boundary_failures : ★0 件
```
**原因（コード逐語）:**
```
再現: grep -n "def _trace" -A 3 twoder/webui.py
  94: def _trace(task_id):
  95:     p = RUNS / f"{task_id}.trace.json"
  96:     return json.loads(p.read_text()) if p.exists() else {}

再現: grep -n "trace.json" twoder/webui.py
  545: _atomic_write(RUNS / f"{key}.trace.json", …)      ← webui の /api/submit が書く
  547: if tid: _atomic_write(RUNS / f"{tid}.trace.json", …)  ← ★task_id 名の trace も webui が書く
```
> **∴ `build_state` が読む `<task_id>.trace.json` は、★webui の `/api/submit` だけが書いている。**
> **∴ CLI（`python3 -m twoder.submit`）で投入すると、その file は作られない。**
> **∴ `tr` が空になり、`etrace_run_id` も `boundary_failures` も `rri` も出ない。**

**★これは私が足した2キーの問題ではありません。** **`tr` 由来の既存キー（②の `resolved_intent` 等）も同時に空です。**
**∴ 「2キーを足しても出ない」のではなく、「CLI 投入の task は TRACE を持たない」のが根です。**

### 2-1. 対照（同じ画面が webui 投入の task では出ること）
```
再現: GET /api/state?task_id=TASK-2DER-21F64D9D   （webui から投入された task）
  ★boundary_failures : 2件（DS の2件が出る）
  ★既存キーの ② も出る
```
**∴ 同じコードで、投入経路が違うだけで結果が変わります。**

## 3. ★私はここで止めました（実装源 §6-1）
- **繋げる細工をしていません。** **CLI 投入でも trace を書くようにする、といった修正をしていません。**
- **2回目を投入していません**（MGR 条件1・実装源 §3-1）。
- **★webui から同じ文面をもう一度投入すれば受入1〜3 は満たせる可能性が高いですが、それは2回目の投入です。** **独断で行いません。**

## 4. 受入4・5・6（満たした分）
```
受入4: /api/state の既存キーのみの sha256
       before d6d888bea8334bd0 / after d6d888bea8334bd0  ★一致（消えたキー0・追加は2キーのみ）
受入5: 非回帰98本 91 passed / 7 failed（基準と★顔ぶれ diff 空）
受入6: ★etrace_run_id が None のとき、③のカードは「この依頼の run_id は記録に無い」を出す実装になっている
       （空欄にしない・カードを消さない）。今回の task がまさにその状態である。
```
**★ただし受入6 は「画面をブラウザで開いて見た」わけではありません。** **JS の分岐がその文字列を出す実装であることと、`etrace_run_id` が `None` である実測の2つを示しているだけです。** **実装源 §7-3 の「画面をブラウザで見ていない」を私も引き継ぎます。**

## 5. 予想と実際（実装源 §4）
| 項目 | 設計の予測 | **実際** | 判定 |
|---|---|---|---|
| **③ が出るか** | **出る方に賭ける** | **★出なかった**（CLI 投入の task は TRACE を持たない） | **★外れた** |
| ⑤ に `boundary_failures` が出るか | 予想しない | 0件（`tr` が空のため） | — |
| event の件数 | 予想しない | 引けていない | — |
| **既存4項目が壊れないか** | **壊れない方に賭ける** | **★壊れていない**（sha256 一致） | **当たり** |

## 6. ★足りないもの（実装源 §5 に1件足します・作っていません）
| # | 足りないもの |
|---|---|
| 4 | **★CLI で投入した依頼を UI で開く手段。** **`<task_id>.trace.json` を書くのが webui だけなので、CLI 投入の task は DW task が在っても中身が出ない。** **実装源 §5-3 の「trace を読む口が無い」の隣に、「CLI 投入は trace を書かない」を並べます** |

## 7. 触ったファイル
```
twoder/webui.py のみ（build_state に2キー追加 / /command の JS にカード2枚追加）
★ids.py・emit・/ ・既存4項目のカード・endpoint には触っていません。
```
**commit していません**（MGR）。

---
*IMPL BUILT（D-49・**受入1〜3 の手前で停止**）。承認文面を1文字も変えず CLI で1回投入し、**`DW_TASK_ID = TASK-2DER-AC13F06E` / `BUILD_CAPABILITY` / `ETRACE_RUN_ID = ETR-88bc41400d19`** を得た（MGR 条件1 の「BUILD_CAPABILITY にならなければ止める」には当たらない）。★しかし `GET /api/state?task_id=TASK-2DER-AC13F06E` では `etrace_run_id` も `boundary_failures` も `rri.resolved_intent` も出ない。原因を決定論で確定=`build_state` が読む `<task_id>.trace.json` は **webui の `/api/submit` だけが書いており**（`webui.py:545,547`）、**CLI 投入ではその file が作られない**ため `tr` が空になる ∴ **私が足した2キーの問題ではなく、`tr` 由来の既存キーも同時に空**であり、根は「CLI 投入の task は TRACE を持たない」こと。対照として webui 投入の `TASK-2DER-21F64D9D` では同じコードで `boundary_failures` が2件出る。★実装源 §6-1「`etrace_run_id` を足しても出ない → 私の見立てが外れた。報告する」に該当するので、**繋げる細工をせず、2回目も投入せずに止めた**（webui から投入すれば満たせる可能性が高いが、それは2回目なので独断で行わない）。満たした分=受入4（既存キーのみの sha256 が `d6d888bea8334bd0` で前後一致・消えたキー0・追加は2キーのみ）／受入5（非回帰 91/7・顔ぶれ diff 空）／受入6（`etrace_run_id` が `None` のとき「run_id は記録に無い」を出す実装であり、今回の task がその実例）——**ただしブラウザで画面を見たわけではなく、JS の分岐と実測値の2つを示しただけ**であることを明記。予想は「③が出る」が★外れ、「既存が壊れない」が当たり。★足りないもの4件目を追加（**CLI で投入した依頼を UI で開く手段**——`<task_id>.trace.json` を書くのが webui だけなので CLI 投入は DW task が在っても中身が出ない）。触ったのは `twoder/webui.py` のみで commit していない。*
