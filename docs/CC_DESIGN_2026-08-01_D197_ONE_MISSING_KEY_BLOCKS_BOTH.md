# 【調査回答 / D-197】**★`_MAP` に `JUDGE_REQUIRED` が無い** — ★D-196 と D-197 の閉塞は★同じ1本

- `BUILD_ROLE: 参照` / **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-08-01 00:5x / TYPE=FINDING
- **開発者規律 確認済（版: v1.0 / 2026-07-31）** ／ **受領**: `D-197`（3値で返す・コード0行）
- **この .md がまだ .md である理由**: 回答を台帳へ書く口が front door に無いため（C-1）
- **★コードを1行も変えていない ／ ★増やした管理対象 0**

---

# 1. ★(a) Claude の上級監査の答えを 2DER へ戻す口 → **★在って動く。★ただし今の状態からは使えない**

## 1-1. ★口は在る（★逐語）
```
★`twoder/webui.py:371-384`（★全文を読んだ）:
   def ingest(task_id, actor_role, result):
       """Ingest a bounded Claude-actor result into DW; state advances via the real records."""
       ...
       if   op == "PLAN":          W.record_plan(...,          "claude-manager")
       elif op == "DISPOSE":       W.record_disposition(...,   "claude-manager")
       elif op == "UPPER_REVIEW":  W.record_upper_review(...,  ★"claude-senior")
       else: raise ValueError(f"no Claude ingest for op={op}")
★★＝ ★`POST /api/ingest` は ★Claude の答えを ★3段（PLAN / DISPOSE / UPPER_REVIEW）について★受け取り、
   ★★`record_*` で ★台帳へ書き、★状態を進める。★Taka の構想の「戻す口」は ★存在する。
```

## 1-2. ★★しかし、今 止まっている状態からは使えない（★叩いて確かめた）
```
★★★実測（★POST /api/ingest, task=TASK-2DER-E8F8CA7B, actor_role=CLAUDE_SENIOR）:
   ★逐語の返り値: {"error": ★"ValueError: no Claude ingest for op=BLOCKED"}
★★原因（★決定論・`dev-workcell/dw/dispatch.py:28-37` の `_MAP` ★全8件を列挙して確認）:
   CREATED / READY_FOR_IMPLEMENTATION / READY_FOR_AUDIT / DISPOSITION_REQUIRED /
   READY_FOR_REGENERATE / READY_FOR_UPPER_REVIEW / COMPLETE / BLOCKED
   ★★★`JUDGE_REQUIRED` は ★この8件に★入っていない。
★★同 `:53` 逐語: `op, role, input_ref, claude_barrier = _MAP.get(state, ★("BLOCKED", "-", "-", True))`
   ∴ ★`JUDGE_REQUIRED` は ★既定値の `BLOCKED` に落ちる。
★★★★∴ ★2DER は `claude_packet` で「★Bounded review をしてくれ」と★出しているのに、
   ★★その答えを★受け取る先が ★`BLOCKED` になっていて ★受け取れない。
```

## 1-3. ★3値
> ### **★在るが配線されていない。** 繋がっていないのは **★`JUDGE_REQUIRED` → `UPPER_REVIEW`（`CLAUDE_SENIOR`）の1本。**

---

# 2. ★★D-196 と D-197 は、★同じ1箇所である（★これが今回いちばん大きい）

| 見えていた症状 | 出所 | 原因 |
|---|---|---|
| 保留から**再開できない**（`run_next` が BLOCKED） | `D-196` (a) | **`_MAP` に `JUDGE_REQUIRED` が無い** |
| 上級監査の答えを**戻せない**（`ingest` が ValueError） | `D-197` (a) | **同上** |

```
★★2つの別々の閉塞に見えていたが、★★原因は ★`_MAP` の ★キー1つである。
★★★∴ ★ここを繋ぐと ★2つ 同時に解ける ＝ ★規律9（一つ進めるために二つ増やさない）の★逆になっている。
★★★★★「保留」も「上級監査」も ★新しく作る必要が ★無い。★★どちらも ★既に在る。
```

## 2-1. ★ただし断定しないこと
```
★`JUDGE_REQUIRED` が `_MAP` に無いのが ★取り違えなのか ★意図（★人間が必ず見る所）なのかは
   ★私には決められない。★★`D-191`（意図が記録に在るか）は ★止まったままである。
★★∴ ★私は「バグである」と書かない。★「★同じ1箇所である」までを書く。
★★★繋ぎ方も書かない（★裁定の手番を飛ばさない。★`D-196` §3 で材料は出してある）。
```

---

# 3. ★(b) 申請書（依頼テンプレ＝契約の雛形）を 2DER 自身が作る経路 → **★無い**

```
★探索範囲: ★`twoder` と `dev-workcell` の ★`*.py` 全数（★打ち切り無し）
★★`SKELETON` / `skeleton` を含むファイル ★11件 — ★内訳を全部 見た:
   ★`contract_seal.py`（★読む側＝抽出）／ `generate_via_runner.py`（★使う側）／ `webui.py`（★通す側）
   ★`workcell.py`（★保持する側）／ `probe/conformance_probe.py`（★検査）／ ★残り6件は ★`test_*`
★★★★`<<<2DER:` マーカーを ★出力する側（★雛形を作って人や Qwen に渡す側）は ★★0件
   （★`contract_seal.py` と `test_*` を除いた出現数 = ★0）
★★∴ ★契約を ★読む・使う・保持する・検査する 仕組みは ★4つ在るが、
   ★★★契約を ★★作る 仕組みは ★1つも無い。
★★★★参考: ★`dev-workcell/dw/plan_template.py` に ★`template_plan` / `create_knowledge_packet` /
   `plannable` は在る。★ただしこれは ★PLAN の雛形であって ★依頼文（申請書）の雛形ではない。
```

## 3-1. ★これは C-2 と同じものである（★増やさない・`D-197` §3(b) のとおり）
```
★★「申請書が無いと困る」＝ ★依頼を出す側に ★決まった型が無い、である ＝ ★C-2（入口を固定する）。
★★★Taka の構想では ★作るのは ★2DER である ∴ ★我々は雛形を書かない。★依頼して作らせる。
★★★★∴ ★C-2 の依頼文には ★「★契約の雛形を出す口を作れ」が入る。★S-3 と同じ形（★受入試験つき）になる。
```

---

# 4. ★循環の条件（`D-197` §4）について、★測り方だけ先に置く（★決めるのは MGR）
```
★MGR が固定した3条件のうち ★③「★同じ穴で Claude が呼ばれた回数が減る」は ★機械で数えられる:
   ★`POST /api/ingest` の ★`actor_role` 別・★`op` 別の回数（★front door を通るので記録に残る）
★★①②（★書き戻る／★次は Qwen だけで通る）は ★今のところ ★数える口が無い【未確認】。
★★★∴ ★「循環した」と言うのは ★③が減った時だけにする。★①②は ★口ができてから。
★★★★★私は ★数を作っていない。★測り方を書いただけである。
```

---

# 5. ★やっていないこと
```
★コードを1行も変えていない ／ ★`_MAP` に触っていない ／ ★繋ぎ方を書いていない
★契約の雛形を書いていない（★2DER に作らせるもの）／ ★新しい計器・台帳・状態語を作っていない
★S-3 に手を出していない（★ACTIVE は S-3 のまま。★IMPL の手番）
★`D-191` は止めたまま ／ ★上級監査の答えを .md に書いていない（★`D-197` §4 のとおり）
★★★`POST /api/ingest` は ★1回 叩いたが ★`ValueError` で ★台帳は変わっていない
   （★`ingest` は ★`record_*` の★前に raise する ∴ ★書き込みは起きない。★コードで確認済）
```

---
**決めたこと**: **①Claude の答えを 2DER へ戻す口は在って動く——`POST /api/ingest` が PLAN / DISPOSE / UPPER_REVIEW の3段で `record_*` を呼び、台帳へ書いて状態を進める ②しかし今 止まっている状態からは使えない。叩いて確かめた返り値は `ValueError: no Claude ingest for op=BLOCKED` ③原因は `_MAP` の全8キーに `JUDGE_REQUIRED` が無く、既定値の `BLOCKED` に落ちること ④∴ 3値は「在るが配線されていない」。繋がっていないのは `JUDGE_REQUIRED` → `UPPER_REVIEW` の1本 ⑤★D-196（保留から再開できない）と D-197（上級監査の答えを戻せない）は、別々の閉塞に見えて原因が `_MAP` のキー1つで同じである。繋ぐと2つ同時に解ける ⑥ただし取り違えか意図かは決めず「バグ」と書かない。繋ぎ方も書かない ⑦(b) 契約の雛形を作る仕組みは無い——読む・使う・保持する・検査する側は4つ在るが、マーカーを出力する側は 0件。`plan_template` は PLAN の雛形であって申請書の雛形ではない ⑧これは C-2 そのものなので別件にしない。作るのは 2DER であり我々は雛形を書かない ⑨循環の③（Claude が呼ばれた回数）は `/api/ingest` の actor_role 別・op 別で機械で数えられるが、①②は数える口が無い。∴「循環した」と言うのは③が減った時だけにする。**
