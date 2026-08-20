# 実 repo 反映の 因果鎖 ―― ★全件検索ベース（★実装 0 ／ ★コード 0行）

**2026-08-20 19:4x ／ ★Taka 裁定「接続を作ってよい。ただし実装前にこの一本の因果鎖を全件検索ベースで確定してから」**

---

## 0. ★探した 範囲（★「無い」と 言う 前に 書く）

```
★`git add` / `git commit` / `shutil.copy` / `place` / `_place_and_commit`  … 全件
★`energize` / `def mint` / `_EnergizedApply`                              … 全件
★`ENERGIZATION_ADJUDICATION`                                              … 全件
★`reconcile(` / `latest_balance_proof`                                     … 全件
★`files_expected` / `target_repositories`                                  … 全件
★対象 = `twoder` ／ `dev-workcell`（★`runs/` と `regression/` を 除く＝★本番のみ）
```

---

## 1. 因果鎖（★12点 ―― 誰が作る / 誰が読む / どこで止まる / 失敗時どこへ）

| # | 点 | 誰が作る | 誰が読む | どこで止まる | 失敗時どこへ |
|---|---|---|---|---|---|
| 1 | **2DER GENERATE** | `webui` の `cw` → `generate_via_runner` | `record_generate` | 骨格検査 ／ 試験 | `test_result.passed=False` → AUDIT へ |
| 2 | **artifact** | `qwen_worker`（sandbox の 単一 file） | `claude_packet.test_result.artifact` | `check_artifact`（長さ・SHA） | `receivable=False` → 受領しない |
| 3 | **既存file変更が必要か** | **★★誰も 判定しない** | ― | ― | **★★空白** |
| 4 | **source_to_patch** | `twoder/source_to_patch.py`（★私が 作った） | **★★本番の 呼び手 0** | ― | **★★空白** |
| 5 | **patch validation** | `patch_bridge.canonical_diff_artifact` / `validate_artifact` | `apply_cycle` | `allowed_files` 違反 ／ 新規 file ／ base 不一致 | `ValueError`（fail-closed） |
| 6 | **authority** | **★★誰も `ENERGIZATION_ADJUDICATION` を 書かない**（★全件検索＝読むのは `bridge_minter` だけ） | `bridge_minter.mint_real_energize` | **門(1) 裁定 event が 無い** | `MintRefused` |
| 7 | **apply_cycle** | `twoder/apply_cycle.py` | **★★呼び手 0** | 単一 file ／ dry-run | `REFUSED_MULTI_FILE` 等 |
| 8 | **rollback / reconciler** | `patch_bridge`（rollback）／ `bridge_reconciler`（proof） | `apply_cycle` ／ `bridge_minter:126,148` | ★balance が 古い → 門(3) | `MintRefused` |
| 9 | **実 repo 変更** | ★(a)`_place_and_commit`（**稼働中**）／ ★(b)`apply_cycle`（**未接続**） | git | (a) 関数名が 読めない ／ twoder の 外 ／ 中身が 同じ ／ 構文が 壊れている | 語で 返す |
| 10 | **再実走** | `run_until_barrier`（MGR が 叩く） | dispatch | 既存の 各門 | 既存経路 |
| 11 | **observed edge** | 各段の `_HO("Sxx")` → `etrace` | `_observed_edges_of` | ― | 空集合 → fail-closed |
| 12 | **COMPLETE** | `dispatch:77` → `webui:1592` → `return_loop` → `propose_complete:597` | `completion_blockers` | blocker が 1本でも 在れば | `WorkflowViolation` |

---

## 2. ★★埋まらなかった 点（★3つ ―― ★これが 結論）

```
★★#3 「既存file変更が必要か」を ★判定する 者が 居ない。
   ★PLAN には `files_expected`(★逐語「files or artifact classes to be created/modified」)と
     `target_repositories` が 在る が ―― ★全件検索の 結果 ★★読むのは `build_planner` の
     ★『空でないか』検査だけ（`:277-278` の malformed 検査）。
   ★★＝ ★『新規か 変更か』を 分ける 判定は ★1つも 存在しない。

★★#4/#7 `source_to_patch` と `apply_cycle` は ★本番の 呼び手 0（★本日 2度 確認）。

★★#6 ★★`ENERGIZATION_ADJUDICATION` を ★書く 者が ★本番に 1つも 無い。
   ★全件検索 = ★出現は `bridge_minter` の 3箇所のみ（★すべて ★読む 側）。
   ★さらに ★`PROCESS_EVENT_KINDS`(★DW が 受け付ける 記録の 語・9語)に
     ★★`ENERGIZATION_ADJUDICATION` は ★★入って いない。
   ★★∴ ★裁定 event を ★記録する 経路 自体が ★存在しない。
   ★★∴ ★門(1)「裁定 event が 在る」は ★★構造上 満たせない ＝ ★`mint_real_energize` は 常に `MintRefused`。
```

---

## 3. ★★∴ いま 接続を 作っても 通らない（★実装前に 分かった）

```
★仮に ★#4→#7 を 繋いでも ―― ★#6 で 必ず 止まる。
   ★`apply_cycle` は `energize` を 引数で 受ける。
   ★実 repo の `energize` を 出せるのは `bridge_minter.mint_real_energize` だけ。
   ★その 門(1)が ★裁定 event を 要求し ★その event を ★書く 者が 居ない。
★★＝ ★接続を 1本 足しても ★実 repo は 1バイトも 変わらない。
★★＝ ★『部品は 在る が 呼び手 0』が ★★2段 重なって いる（#4/#7 と #6）。
```

**★★これが 私が 前回 見落とした もの と 同じ 型 です。★今回は 実装前に 出しました。**

---

## 4. ★選べる 道（★私は 決めない ―― ★どれも 設計判断）

| 案 | 中身 | 触る もの |
|---|---|---|
| **あ** | `ENERGIZATION_ADJUDICATION` を **DW の記録語彙に 1語 足す** ＋ Taka が 裁定を 記録する 口を 決める | ★`PROCESS_EVENT_KINDS`（★新語 1）／ ★authority 境界に 触れる |
| **い** | `_place_and_commit` の **置き先の決め方**を 「関数名 → 新規 file」から 広げる | ★既存の 稼働機構を 変える ／ ★authority 門を 通らない |
| **う** | 第四の 変更を **既存 file の 変更では なく 新規 file** で 表せる 形に 設計し直す | ★2DER 側の 設計 ／ ★`_place_and_commit` は そのまま 使える |

```
★★「あ」は ★安全境界(authority)に 触れる ∴ ★★Taka 以外が 決められない。
★★「い」は ★稼働中の 機構を 変える ∴ ★回帰の 危険が 大きい。
★★「う」は ★安全境界を 1つも 触らない が ★第四の 中身を 変える（★schema 変更は 既存 file）
   ―― ★`build_planner.py` を 変えずに `linkage` を 足す 方法が 在るかは ★私には 判らない（★UNVERIFIED）。
```

## 5. ★していないこと

```
★実装 0 ／ コード 0行 ／ repo 変更 0 ／ 投入 0
★`ENERGIZATION_ADJUDICATION` を ★書いて いない ／ ★語彙を 増やして いない
★`_place_and_commit` を ★呼んで いない（★私への 禁止は 継続）
★SELF_DEV_TOKEN = ★5/5
```
