# 宛: Taka ―― **run-gate 調査: ★答えは B（★但し 重要な 但し書き つき）**

**2026-08-20 06:4x ／ ★調査のみ ／ ★`_GATES` への 書き込み 0 ／ ★gate 強制発行 0 ／ ★run_next 0**
**★guard 無効化 0 ／ ★authority 変更 0 ／ ★safety boundary 変更 0 ／ ★実装 0**

---

## Q1 ★`_GATES` は どの 処理で 生成されるか（★全4箇所・★実測）

| 場所 | 何を する | 前提 |
|---|---|---|
| **`webui.py:1452`** | **★初回の 発行**（submit の 中） | ★`/api/submit` の 処理を 通ること |
| `webui.py:1533` | ★`runnable=True` へ 差し替え（★REARM） | ★`/api/run_*` の 中 ／ ★**gate が 既に 在ること** |
| `webui.py:1586` | `runnable=False`（PROPOSE_COMPLETE 後） | ★run の 中 |
| `webui.py:1595` | `runnable=…` を 更新（run_next 後） | ★run の 中 |

```
★保存/復元 = `_GATES_FILE = twoder/runs/gates.json` ／ `:1951 _gates_load()`（★起動時に 読み直す）
★★＝ 復元は ★『前に 発行した 門』を 読み戻すだけ ―― ★新しく 生む 経路では ない。
★★∴ ★★門を ★0 から 生む 場所は ★`:1452`（submit）★1箇所だけ。
```

## Q2 ★gate 生成に 使う 入力・証拠・authority（★逐語）

```
★`webui.py:1439-1454`（実物）:
   tid      = tr.get("DW_TASK_ID")
   blocked  = bool(tr.get("GUARD_BLOCK"))
   runnable = bool(tid) and not blocked
   _gate_put(tid, blocked=blocked, runnable=runnable, reason=…)
```

```
★★＝ 入力は ★2つ だけ ―― ★① task が 出来たか（`DW_TASK_ID`）
                          ★② guard が 止めたか（`GUARD_BLOCK`）
★★＝ ★authority の 語も 承認の 記録も ★1つも 使っていない。
```

## Q3 ★後から 正規に mint / rearm / restore する 経路は 在るか

```
★rearm  … ★在る（`:1512-1536`）―― ★但し ★`decide_rearm_v2` の ★第1引数が
          `_GATES.get(tid) is not None`＝★**gate_present**
          ★`decide_rearm_v2.py:17` 逐語「1. ★gate_present が偽なら "MISSING_GATE"。」
          ★★∴ ★門が 無い task は ★rearm できない（★★今回の 停止理由 そのもの）。
★restore … ★在る（`_gates_load()`）―― ★但し ★★保存済みの 門を 読み戻すだけ。
★mint    … ★★`:1452`（submit）以外に ★存在しない。
```

## Q4 ★既存部品の うち bootstrap task に そのまま 使える もの

| 部品 | 使えるか | 理由 |
|---|---|---|
| `gate_decision` | ★使える | ★門を 読んで 3理由に 分けるだけ |
| `decide_rearm_v2` | **★使えない** | ★`gate_present` を 要求（★今回 False） |
| `task_findings` | ★使える | ★task から 引く |
| `_machine_registry()` / `_MAP.claude_barrier` | ★使える | ★task から 引く |
| `receipt` / `token` / `authority` | ★関係しない | ★gate 生成に ★使われていない（Q2） |

```
★★＝ ★`gate_present` の ★1点を 除けば、★判定に 要る 材料は ★すべて ★task 自身から 引ける。
```

## Q5 ★★★確定 ―― **gate は「Front Door を 通った」ことを authority に していない**

```
★★★後者。★Front Door は ★別の 証拠（★DW_TASK_ID の 有無 ／ ★GUARD_BLOCK の 有無）を
   ★まとめて 門を 発行しているだけ。
★根拠 = ★`:1440` の 2行が ★門の 全内容（★Q2 逐語）
★★＝ ★『front door 由来』という ★資格そのものは ★門の 中に 1文字も 無い。
★（★2026-08-18 の コメント 逐語も 同じ 向き:
   「★認可の 鍵を『現在の submit context』から ★『task 自身の 証拠』へ 寄せる ための 最小配線」）
```

**★同じ 証拠を 既存の 正規経路で 満たせるか:**

```
★① `DW_TASK_ID` が 在る … ★★満たせている（★`TASK-2DER-D7977C1A` は 実在・provenance ok=True）
★② `GUARD_BLOCK` が 無い … ★★満たせている（★この task の 記録に GUARD_BLOCK は 無い）
★★∴ ★★『門を 発行してよい 証拠』は ★★既に 揃っている。
★★但し ―― ★それを ★門に する 経路が ★submit の 中にしか 無い。
```

## ★★最終回答 ―― **B**

```
★★B. 正規の 発行経路は ★Front Door 専用 ―― ★maintenance task を 走らせる 手段が ★存在しない。

★★但し 但し書き（★正確に 書く）:
   ・★『front door を 通った ことが authority』では ★ない（★Q5）
   ・★門の 材料は ★2つとも ★bootstrap task で ★既に 満たされている
   ・★足りないのは ★★『その 2つから 門を 生む 呼び手』が ★submit の 外に 無い こと だけ。
```

## ★★不足している 最小能力（★1つだけ・★実装しない）

```
★★『既に 存在する task に ついて、★`DW_TASK_ID` が 在り ★`GUARD_BLOCK` が 無い ことを
   確かめた うえで ★初回の 門を 1つ 立てる』呼び手。

★★これが 無い ため:
   ・★rearm は 使えない（★gate_present=False で 即 MISSING_GATE）
   ・★restore は 使えない（★保存済みの 門しか 戻さない）
   ・★submit は 使えない（★GUARD が この 依頼 自身を 止める＝★第1層）
★★∴ ★二重の 封鎖は ★『門を 生む 呼び手が 1つ 足りない』に ★収束する。
```

## ★していないこと

```
★`_GATES` への 直接書き込み 0 ／ gate 強制発行 0 ／ `gates.json` への 書き込み 0
★run_next 0 ／ guard 無効化 0 ／ authority 変更 0 ／ safety boundary 変更 0
★実装 0 ／ 修正 0 ／ 新しい 呼び手 0 ／ ★2DER への 投入 0
★実 repo 書き込み 0（★twoder HEAD `24c649a` 不変）／ ★常駐 停止のまま
★SELF_DEV_TOKEN = ★5/5
```
