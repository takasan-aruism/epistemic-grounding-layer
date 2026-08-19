# 宛: Taka ―― **制御面 bootstrap 一周の ★受入基準（★結果より 先に 固定）**

**2026-08-20 06:5x ／ ★走行中に 書いた（★結果を 見る 前）**
**★SELF_DEV_TOKEN = ★5/5（★一周が 閉じた 時のみ 1消費）**

---

## 0. ★なぜ 先に 書くか

```
★結果を 見てから 基準を 作ると ★都合よく 読める。
★★今夜 7回 出た 型（★作れる ／ 繋がらない）を ★『成立』と 誤読しない ため、
  ★★何を もって ①〜⑥ と するかを ★走行中の いま 固定する。
```

## 1. ★★①〜⑥ の 判定（★機械の 値だけで 決める）

| # | Taka の 条件 | ★合格と する 実測値 | ★不合格の 例（★先に 書く） |
|---|---|---|---|
| **①** | `TASK-2DER-D7977C1A` に 初回 gate が ★正規生成される | ★`_gate_get("TASK-2DER-D7977C1A")` が ★`task_id` を 持ち ★`runnable=True` ／ ★生成が ★2DER の 作った 経路 経由 | ★MGR が `_GATES` を 触った ／ ★`gates.json` を 手で 書いた ＝ ★★即 不合格 |
| **②** | `MANAGER_V0_ONCE` が ★MISSING_GATE で なく PLAN へ 進む | ★tick の 返りが ★`SLEEP/MISSING_GATE` で ★無い ／ ★`derive_state` が ★`CREATED` から 動く | ★`SLEEP` の まま ＝ 不合格 |
| **③** | 以後 通常の PLAN → GENERATE → TEST → AUDIT | ★`phase` に ★`PLAN` `GENERATE` `AUDIT` が 並ぶ | ★`PROCESS_EVENT` だけ ＝ 不合格 |
| **④** | GUARD false match 修理を ★2DER 自身が 実装 | ★`D7977C1A` の `GENERATE` に ★artifact_sha256 が 在り ★`passed=True` | ★MGR が コードを 書いた ＝ ★★即 不合格 |
| **⑤** | 修理後 ★通常 Front Door から 元依頼を 再投入し ★false BLOCK が 消える | ★`goal25`（★safety / deliverable を 含む 原文）を ★`/api/submit` へ 投げ、★`acquisition_method` が ★`BLOCKED_DEAD_APPROACH` で ★無い | ★まだ BLOCK ＝ 不合格 |
| **⑥** | 本来 BLOCK すべき ★復活依頼は ★引き続き BLOCK | ★`AFE` / `formal ESDE` / `structural operator` を ★live detector と して 復活させる 文を 投げ、★`BLOCKED_DEAD_APPROACH` が ★出る | ★通ってしまう ＝ ★★即 不合格（★安全側の 後退） |

```
★★⑤と⑥は ★対で 測る ―― ★片方だけでは ★『緩めただけ』と ★区別が つかない。
★★⑥の 試験文は ★MGR が 書く（★2DER の 実装物では ない ＝ ★独立した 確認）。
```

## 2. ★★『成立』と 呼ばない もの（★先に 明記）

```
★★sandbox で 補助関数が ★PASS した だけ ＝ ★不合格（★今夜 7回 出た 型）
★★`D7977C1A` が ★動かない まま 別の task が 通った ＝ ★不合格
★★MGR が 門を 立てた ／ 記録を 書き換えた ＝ ★不合格
★★⑤だけ 通って ⑥が 通らない ＝ ★不合格（★安全側の 後退）
```

## 3. ★token の 扱い

```
★★①〜⑥が ★全部 揃った 時のみ ★SELF_DEV_TOKEN を ★1 消費する。
★1つでも 欠けたら ★消費しない（★5/5 の まま 報告する）。
```

## 4. ★MGR が この 周で している こと / していない こと

```
★している = 投入 ／ 監視 ／ 事実確認 ／ 記録 ／ commit・push
★★していない = 実装 ／ `_GATES` への 書き込み ／ `gates.json` の 手書き ／ `run_next`
   ／ guard・failure memory・authority・安全の 境界・範囲 の 変更
★★依頼文の 走査を 事前に 行った（★afe / live を 含む 語 = ★0件）
   ―― ★これは 迂回では ない（★主題が 門の 生成 ／ ★制約は 日本語で 自然に 書ける）
   ★対照: ★BLOCK された 依頼は ★一致規則 自体が 主題 ∴ ★その 語を 書かざるを 得なかった
```
