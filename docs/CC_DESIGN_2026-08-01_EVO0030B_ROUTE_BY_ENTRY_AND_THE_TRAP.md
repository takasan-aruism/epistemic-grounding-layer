# 【BUILD SPEC / `EVO-0030` 追補】入口でも行き先を決める — **★ただし「入口」の読み方に罠が在る**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-01 13:3x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.1 / 2026-08-01）** ／ **裁定**: `D-208` §1（Taka 追加指示・受入(e) を追加）
- **★新しい名前で置いた**（★前 SPEC を同名で差し替えない）／ **★私はコードを1行も変えていない**
- **この .md がまだ .md である理由**: 指示を台帳へ渡す口が無いため（★`EVO-0022` / C-2）

---

# 0. ★★先に罠を潰す（★今日4度目にしない）

> ### **★`derive_state` のループの中の `state` は、★`/api/state` が返す state と★一致しない。**

```
★逐語（`dev-workcell/dw/workcell.py`）:
   ★`:131`     `for e in evs:`            ← ★ループ開始。★ここで `state` が更新されていく
   ★`:202`     `if state in ("READY_FOR_REGENERATE","DISPOSITION_REQUIRED")
                 and view["rework_count"] >= REWORK_ESCALATION_THRESHOLD: state = "JUDGE_REQUIRED"`
                                          ← ★★★ループの★外。★最後に1回だけ当たる
★★★∴ ★`UPPER_REVIEW` の分岐が★ループの中で見る `state` は ★★昇格前の値である。
★★★★実例（★今回の task）: ★外から見えるのは ★`JUDGE_REQUIRED` だが、
   ★ループの中では ★`READY_FOR_REGENERATE` である。★★2つは違う。
★★★★★★∴ ★★素直に `state` を「入口」として使うと、★★Taka が求めた区別に ★ならない。
```

## 0-1. ★∴ 入口の定義（★これを使う）
```python
# UPPER_REVIEW の分岐の先頭で
_entry = state
if _entry in ("READY_FOR_REGENERATE", "DISPOSITION_REQUIRED") \
   and view["rework_count"] >= REWORK_ESCALATION_THRESHOLD:
    _entry = "JUDGE_REQUIRED"        # ★:202 と同じ規則を、★同じ形でここにも当てる
```
```
★★★これは ★規則を2箇所に持つことになる ∴ ★好ましくない。★私は好ましくないと書く。
★★★★★しかし ★`:202` をループの中へ移すのは ★★既存の全 task の state を変えうる（★可逆でない）。
   ∴ ★★今回は ★写す方を採る。★★「★2箇所に在る」ことを ★コメントに1行 書くこと。
★★★★★★畳む条件（★併記する）: ★`:202` をループ内へ移して1箇所にできること。
   ★★足りないもの: ★既存 task への影響を測る手段。★今回は作らない。
```

---

# 1. ★分岐（★入口 × 判定。★本数と条件は私が決める・`D-208` §1）

```python
elif ph == "UPPER_REVIEW":
    view["upper_reviews"].append(e)
    _entry = <★§0-1 のとおり>
    v = ("%s" % ((pl.get("review") or {}).get("verdict") or "")).upper()
    if   v == "PASS" and bool(view.get("last_test_passed")):
        state = "READY_FOR_UPPER_REVIEW"      # ★完了 gate へ（★入口を問わない・§1-1）
    elif v == "FAIL" and _entry != "JUDGE_REQUIRED":
        state = "READY_FOR_REGENERATE"        # ★通常の道から来た FAIL → 作り直す余地が在る
    elif v == "FAIL":                         # ★＝ 入口が JUDGE_REQUIRED
        state = "JUDGE_REQUIRED"              # ★★作り直しへ戻さない（★§1-2）
    else:
        state = "JUDGE_REQUIRED"              # ★INDETERMINATE / 空 / 知らない値 / PASS だが試験未通過
```

## 1-1. ★`PASS` は入口で分けない（★理由を書く・`D-208` §1「同じでよいなら理由を書く」）
```
★`PASS` かつ ★試験通過は ★「★成果物が在り、★試験が通っている」という★事実の主張である。
★★どの入口から来ても ★その事実は★変わらない ∴ ★分けない。
★★★★かつ ★`PASS` だが試験未通過は ★★既に4本目（人へ）で拾っている ∴ ★入口を見る必要が無い。
```

## 1-2. ★★`FAIL` は入口で分ける（★これが Taka の指摘の中身）
```
★入口 `READY_FOR_UPPER_REVIEW` からの `FAIL` → ★作り直しへ。★★rework が残っている ∴ ★意味が在る。
★★入口 `JUDGE_REQUIRED` からの `FAIL` → ★★作り直しへ戻さない。
   ★理由: ★★`JUDGE_REQUIRED` は ★rework を使い切った印である（`:41` 逐語
   `REWORK_ESCALATION_THRESHOLD = 2   # rework がこの回数を超えたら JUDGE_REQUIRED へ強制昇格`）。
   ★★★戻せば ★`:202` が ★即座に ★`JUDGE_REQUIRED` へ★押し返す ＝ ★★同じ場所を回るだけである。
   ★★★★★これは ★Taka 逐語「★同じ場所へ ★何度も戻す形になりうる」★そのものである。★★今回 実測もした。
★★★★★★∴ ★行き先は ★`JUDGE_REQUIRED` のまま。★★ただし ★意味が変わる:
   ★以前 = ★「昇格規則の★副作用でそこに居る」／ ★以後 = ★「★分岐が★意図してそこへ置いた」
```

---

# 2. ★受入（★`D-208` §1 の (e) を足す。★★測れる task で測る）

```
★★★★測定用の task を ★1つ 立てる（★rework 未使用）。★★本番の1件（`TASK-2DER-B37727E3`）は
   ★★(c) の確認にだけ使う（★★私が前 SPEC で測れない task を指定した誤りを繰り返さない）
★(a) ★入口 `READY_FOR_UPPER_REVIEW` ＋ `FAIL` → ★`READY_FOR_REGENERATE` へ★動く
★(b) ★`PASS` ＋ 試験通過 → ★`next_operation` が ★`PROPOSE_COMPLETE`
★(c) ★`review` 本文が ★`GET /api/state` の ★`upper_reviews` から読める（★★済・再確認のみ）
★(d) ★`INDETERMINATE` / 知らない値 / `PASS` だが試験未通過 → ★`JUDGE_REQUIRED`
★★(e) ★★入口 `JUDGE_REQUIRED` ＋ `FAIL` → ★`READY_FOR_REGENERATE` に★ならない
   ★★★＝ ★(a) と (e) を ★同じ `FAIL` で ★並べて示す。★★1件では足りない（`D-208` §1）
★★★★★★予告を投入前に書く: ★(a)〜(e) の予想 ／ ★変更行数 ／ ★立てる task の id（★sha1 から先に出す）
```

---

# 3. ★誰が書くか（★`D-208` §3 の既定を当てる）
```
★★`dev-workcell` は ★本番 repo ∴ ★worker には書かせられない（★`PROD_REPO_ROOTS` に在る・★決定論で拒否）。
★★★∴ ★★あなたが書く。★★行数を必ず報告し、★2DER の実績に★数えない。
★★★★★今回は ★試さなくてよい（★`D-208` §3 で ★既定になった）。★★「既定に従った」と1行 書くこと。
```

# 4. ★禁止 ／ 5. ★報告
```
【禁止】★`:202` の昇格規則を ★動かす（★可逆でない・★§0-1 に理由）／ ★新しい state 名を作る
        ★`_MAP`/`_ALLOWED` を触る ／ ★新しい台帳・計器・マーカーを作る ／ ★commit する
        ★★`review` の中身を創作する（★判定は設計/監査と MGR。★★`verdict` は仮でよいが ★`PLACEHOLDER` と書く）
        ★★★本番の1件（`TASK-2DER-B37727E3`）で ★(a)(b)(d)(e) を測る（★測れない）
【報告】1 ★変更行数（★誰が書いたか）／ 2 ★受入 (a)〜(e) ／ 3 ★予告の当否 ／ 4 ★戻し方
        5 ★★「規則が2箇所に在る」ことをコメントに書いたか ／ 6 ★立てた task の id
★宛: 設計/監査(CC-α)。TYPE=BUILT
```

---

# 6. ★行番号の件（★`D-208` §4）— **★受ける**
```
★私は ★`webui.py:221` と名指したが ★実際は ★`claude_packet()` の中だった。
★★以後 ★行番号には ★★関数名を併記する（★`webui.py:221（`claude_packet()` 内）` の形）。
★★★★本 SPEC では ★`workcell.py:202`（★`derive_state()` 内）／ ★`:41`（★モジュール定数）と★併記してある。
```

---
**決めたこと**: **①先に罠を潰した——`derive_state` のループの中の `state` は `/api/state` が返す state と一致しない。昇格規則（`:202`・`derive_state()` 内）はループの外で最後に1回だけ当たるので、ループ内では `READY_FOR_REGENERATE`、外から見ると `JUDGE_REQUIRED` になる。素直に `state` を入口として使うと Taka が求めた区別にならない ②∴ 入口は昇格規則を同じ形で当てた後の値とする。規則が2箇所に在るのは好ましくないと明記し、畳む条件（`:202` をループ内へ移して1箇所にできること）と足りないもの（既存 task への影響を測る手段）を併記した。今回は作らない ③`PASS` は入口で分けない——成果物が在り試験が通っているという事実はどの入口でも変わらないから。`PASS` だが試験未通過は既に4本目で拾っている ④`FAIL` は入口で分ける。`READY_FOR_UPPER_REVIEW` からは作り直しへ、`JUDGE_REQUIRED` からは戻さない——戻せば `:202` が即座に押し返し、同じ場所を回るだけで、これは Taka の「同じ場所へ何度も戻す形」そのもの。行き先は同じ `JUDGE_REQUIRED` だが意味が変わる（昇格規則の副作用から、分岐が意図して置いた場所へ）⑤受入に (e) を足し、(a) と (e) を同じ `FAIL` で並べて示させる。測定用の task を1つ立て、本番の1件は (c) の再確認にだけ使う——測れない task を指定した私の誤りを繰り返さない ⑥`dev-workcell` は本番 repo なので worker には書かせられない。`D-208` §3 の既定に従い Claude が書き、行数を報告して 2DER の実績に数えない ⑦行番号には関数名を併記する（`D-208` §4 を受ける）。**
