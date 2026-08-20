# 連動性 照合 ―― `fe46ab5` Stage6 → TRACE → Stage8 分岐（INVESTIGATE）

**2026-08-20 17:2x ／ ★指示書 §13 第三 ／ ★実装 0 ／ repo 変更 0**
**★§7 に 従い ★確定させる 未確定値を 1つだけ 名指しして 測った = ★「調査結果は 後から 正規 API で 取れるか」**

---

## 1. 14項目（★既に 取得済みの 証拠は 再取得して いない）

| # | 項目 | declared | observed（実測） | 一致 |
|---|---|---|---|---|
| 1 | UPSTREAM | `submit.py` の Stage6 直後（`_rec("HANDOFF_CONTRACT")`）／ Stage8 の 先頭分岐 | ★front door 実走で 分岐に 入った（`work_kind=INVESTIGATE`） | **✔** |
| 2 | TRIGGER | `<<<2DER:WORK_KIND>>>INVESTIGATE<<<2DER:END>>>` が 依頼文に 在る こと | 同左（★マーカー無しは `UNDETERMINED` で 分岐に 入らない） | **✔** |
| 3 | INPUT | `raw_input`（★マーカー ／ 問いの 一覧） | 同左 | **✔** |
| 4 | PRECONDITION | Stage4〜7 が 停止して いない こと | 実走で 通過 | **✔** |
| 5 | OUTPUT | `HANDOFF_CONTRACT`(7欄) ／ `INVESTIGATION_REPORT` ／ `EGL_SOURCE_REFS` ／ `STOP_AT_REACHED` | `stop_at_reached=INVESTIGATION_RECORDED` ／ 報告 6件 ／ OBS 4件 | **✔** |
| 6 | DOWNSTREAM | ①`/api/submit` の 応答 ②EGL 観測（`OBS-…`） | 応答に 5欄 出た ／ `GET /api/resolve?id=OBS-05779` が hash つきで 返る | **✔** |
| 7 | STOP | 証拠（`egl_source_refs`）が 記録された 時点で 正常終了 | `task_id=None` ／ `/api/tasks` **566→566**（★task を 作って いない） | **✔** |
| 8 | FAILURE_ROUTE | 例外 → `_fail` ＋ `INVESTIGATION_FAILED` ／ 証拠 0 → `INVESTIGATION_INCOMPLETE` | **★UNVERIFIED**（★実走で 失敗させて いない） | **★未確認** |
| 9 | RECHECK/RETRY/ESCALATE | **★ABSENT** ―― ★宣言して いない | ― | **★ABSENT** |
| 10 | **PERSISTENCE** | TRACE が file に 残り 後から 読める | **★★不一致（下記 §2）** | **✘** |
| 11 | AUTHORITY | ★発行しない（`authority_required="OBSERVE"` は 記録するだけ） | 記録された。★但し ★誰も 読んで いない（呼び手 0） | **PARTIAL** |
| 12 | **EVIDENCE** | `INVESTIGATION_REPORT` ＋ `OBS-…` | ★OBS は 引ける ／ **★報告 本体は 引けない**（§2） | **PARTIAL** |
| 13 | ROLLBACK | `git revert fe46ab5`（★分岐は マーカー依存 ∴ 既存経路に 影響 0） | IMPLEMENT 回帰 実測済（`BUILD_CAPABILITY` → `DW_IMPLEMENTATION` → `PLAN` → task 作成） | **✔** |
| 14 | ROUTE_STAGE | Stage8 = routing | **★CONFLICT** ―― 経路表 `S08` は `contract_seal` を 指す（★段が 別物） | **★CONFLICT** |

---

## 2. ★★私の 前回報告の 訂正（★重要）

**★P1 受入条件 ⑨「調査結果を 正規 API から 後で 取得できる」を ★私は ✔ と 報告しました。★誤りです。**

```
★source だけで 確定（★`runs/` は 読んで いない）:
   webui.py:149   ★読む 側 = RUNS / f"{task_id}.trace.json"       ← ★task_id が 鍵
   webui.py:1443  ★書く 側 = RUNS / f"{key}.trace.json"           ← ★submit ごと
   webui.py:1444  ★`if tid:` の ときだけ {tid}.trace.json を 書く
   webui.py:1459  ★`trace_key` の 出現は ★★1回だけ ＝ ★応答に 載せる 側のみ
                  ＝ ★★`trace_key` を 受け取る 口は ★存在しない
★★INVESTIGATE は `task_id=None` ∴ ★{tid}.trace.json が 作られない
★★∴ ★`INVESTIGATION_REPORT` 本体は ★★即時の HTTP 応答 でしか 取れない。
```

```
★★引ける もの   = ★証拠（`OBS-05779` … ★hash と blob 参照つき）
★★引けない もの = ★★組み立てた M1〜M16 の 調査表 そのもの
★★∴ ★⑨は ★★PARTIAL が 正しい。★私は 証拠が 引ける ことを 見て ★報告 全体が 引けると 早合点した。
```

---

## 3. ★では 直すのか ―― **★直しません**

```
★指示書 §12 の 終了条件 7つ に 当てた:
   ①正規入口から 渡せる / ②2DER が 工程を 進める / ③進行不能 task が 全体を 止めない /
   ④正規停止・再試行・上申 / ⑤経路表・連動性を 無視できない /
   ⑥declared・observed 不一致を COMPLETE に できない / ⑦正規記録から 後で 確認できる
★★INVESTIGATE の 報告が 後から 引けるか は ★この 7つの どれにも 掛からない
   （★①〜⑥の 判断・履歴・証拠は ★task 経由 ＝ `/api/resolve` ／ `/api/state` ／ ROADMAP 台帳 ／
     ★HUMAN_ESCALATION_LEDGER で 引ける ―― ★本日 すべて 実測済）。
★★∴ ★移管の 妨げでは ない → ★§9 に 従い ★移管後へ 送る。
★★読み口を 足すのは ★新機能追加 ∴ ★いま 足さない（★§14）。
```

## 4. ★残す 事実（★隠さない）

```
★① `fe46ab5` は ★★COMPLETE に しない（★PERSISTENCE 不一致 ／ FAILURE_ROUTE 未確認 ／
     RECHECK 未宣言 ／ ROUTE_STAGE CONFLICT）。
★② ★P1 受入 ⑨ は ★✔ では なく ★★PARTIAL（★上の 訂正）。
★③ ★経路表の `S08` と 実物（routing）が 別物 = ★★CONFLICT の まま 残す（★段を 作らない）。
★④ ★`work_kind` が 効くのは ★マーカーが 在る ときだけ ＝ ★既存の 依頼は ★1件も 影響を 受けない（実測）。
```
