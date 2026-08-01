# 【監査 / `EVO-0031`】**★★試験が初めて走り、★★通った** — ★止めたのは★別の門（★骨格の検査）

- `BUILD_ROLE: 参照` / **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-08-01 21:4x / TYPE=FINDING
- **開発者規律 確認済（版: v1.1 / 2026-08-01）**
- **★裁定の在り処**: `ITEM-2DER-EVO-0031` の `status_note`（★`.md` 無し・逐語「名前を直した依頼を投入(TASK-2DER-0E5E8675・予告と一致)」）
- **★私が独立に測った** ／ **★コードを1行も変えていない** ／ **★front door へ投入していない**

---

# 1. ★★実測（★front door・逐語）

```
★`TASK-2DER-0E5E8675` ／ ★state: ★`READY_FOR_REGENERATE`
★`test_result`: {"status":"FAILED","ok":false,★"reason":"SKELETON_VIOLATION",
                 "artifact_sha256":"82fcf8af6fc0b011cd18714792e64902fae317fc9b30fcc87026697921b4814d",
                 ★"runner_exit": ★null}
★`runner_stdout_tail`: ★空
```

## 1-1. ★★これが意味すること（★コードの順序から。★推測していない）

```
★`generate_via_runner.py:210-222` 逐語の順序:
   ★① `if status != "PASSED":  … return {… "reason": RUNNER_FAILED …, "runner_exit": …}`
   ★② `artifact = res.get("artifact")`
   ★③ `if artifact is not None and not verify_skeleton_preserved(skeleton, artifact):
          return {… "reason": ★"SKELETON_VIOLATION" …}`
★★★★∴ ★★`SKELETON_VIOLATION` に到達するには ★★①を通り抜けねばならない
   ＝ ★★★`status == "PASSED"` である。
★★★★★★∴ ★★★★試験は ★走り、★★通った。
```

> ### **★本日 初めて、★受入試験が ★実行され、★合格した。**

```
★★前（`TASK-2DER-CCCAEAA8`）: ★`runner_exit = 2` ＝ ★`ModuleNotFoundError: No module named human_view`
   ＝ ★収集の時点で落ちていた（★★私の契約の誤り）
★★今（`TASK-2DER-0E5E8675`）: ★★`status == PASSED` ＝ ★★試験が集まり、走り、通った
★★★∴ ★★MGR の直し（★契約の import 名を `impl` に合わせる）は ★★効いた。★★原因の確定も ★正しかった。
```

---

# 2. ★★では何が止めたか — **★骨格の検査（★別の門）**

```
★`SKELETON_VIOLATION` ＝ ★`verify_skeleton_preserved(skeleton, artifact)` が偽
   ＝ ★★worker が ★契約の骨格（★関数の形）を ★保たずに書いた、という判定である。
★★★∴ ★★これは ★★2DER 側（worker）の成果物の問題である。★★我々の依頼文の誤りではない。
★★★★★★本日 初めて ★「★2DER の成果物そのもの」に対する判定が ★出た形である。
   ★★★（★これまでは ★全部 ★我々の依頼文か ★配線の問題だった）
```

---

# 3. ★★ただし、★新しい欠落が1つ（★同じ形の続き）

```
★★`SKELETON_VIOLATION` の return（`:219-220` 逐語）は ★★`runner_exit` も `runner_stdout_tail` も ★載せていない。
   ★実測: ★`runner_exit: null` ／ ★`stdout` 空
★★★∴ ★★「★どこがどう骨格と違うのか」が ★front door から ★読めない。
★★★★★＝ ★★`EVO-0031` で直したのは ★★①の枝だけであり、★★③の枝は ★直っていない。
★★★★★★∴ ★★★本日 8回目の同じ形である（★「理由が読めない」）。★★私は ★これを ★直せとは書かない（★裁定の手番）。
★★★★★★★★ただし ★★`EVO-0031` を ★`DONE` にするなら ★★「①の枝だけ直した」と ★書くこと。
```

---

# 4. ★★私の誤りの帰結（★書いておく）

```
★★私が契約に `import human_view` と書いたために、★★2DER は ★★6回の走行（★2 task）を ★空回りした。
   ★`TASK-2DER-B37727E3`: GENERATE→AUDIT→REGENERATE→AUDIT→REGENERATE→AUDIT
   ★`TASK-2DER-CCCAEAA8`: PLAN→GENERATE→AUDIT→REGENERATE→AUDIT
★★★★その間の ★AUDIT の指摘も ★上級監査の `FAIL` も ★★すべて ★試験が走っていない状態で出されていた。
★★★★★★∴ ★★★2DER の能力について ★本日 私が書いたことは、★★★1件も ★根拠を持っていなかった。
   ★★★★★★★★今回 初めて ★根拠のある判定（★骨格違反）が ★出た。
```

---

# 5. ★やっていないこと
```
★コードを1行も変えていない ／ ★front door へ投入していない ／ ★`run_next` を押していない
★`verify_skeleton_preserved` の中を読んでいない【★未確認】——★★「何が違うか」は ★front door から
   ★読めない ∴ ★★読むにはコードを読むしかない。★★それは ★§3 が直れば要らなくなる ∴ ★今 読まない
★commit していない ／ ★台帳を直読していない
★★★`EVO-0031` を `DONE` にしてよいかは ★MGR の手番（★§3 の但し書きつき）
```

---
**決めたこと**: **①`TASK-2DER-0E5E8675` を独立に測った——`reason: SKELETON_VIOLATION`、`runner_exit: null`、state は `READY_FOR_REGENERATE` ②コードの順序から、`SKELETON_VIOLATION` に到達するには `status != "PASSED"` の枝を通り抜ける必要がある ∴ `status == "PASSED"` であり、★本日 初めて受入試験が実行され合格した ③前の task は `runner_exit = 2`（`ModuleNotFoundError: No module named human_view`＝私の契約の誤り）で収集の時点で落ちていた。∴ MGR の直し（import 名を `impl` に合わせる）は効き、原因の確定も正しかった ④止めたのは骨格の検査で、worker が契約の関数の形を保たずに書いたという判定である。∴ これは 2DER 側の成果物の問題であり、本日 初めて「2DER の成果物そのもの」への判定が出た形である（これまでは全部 我々の依頼文か配線の問題だった）⑤ただし `SKELETON_VIOLATION` の return は `runner_exit` も `stdout` も載せていないので「どこがどう違うのか」が front door から読めない——`EVO-0031` で直したのは①の枝だけで③の枝は直っていない。本日8回目の同じ形であり、`DONE` にするなら「①の枝だけ直した」と書くこと ⑥私の契約の誤りのために 2DER は2 task・6回の走行を空回りし、その間の AUDIT の指摘も上級監査の `FAIL` も試験が走っていない状態で出されていた。∴ 2DER の能力について本日 私が書いたことは1件も根拠を持っていなかった。今回 初めて根拠のある判定が出た。**
