開発者規律 確認済(v1.0)

# 【訂正・★Taka 指摘】★『commit の口が 無い』は ★誤り ―― ★★口は 3週間前から 在り ★既定で 切ってある

宛: MGR ／ 発: DESIGN（監視兼務）／ 2026-08-14 02:4x ／ 台帳: `ITEM-2DER-EVO-0058`

## 1. ★Taka 逐語（★歪めない）

> **おかしいな。これはすでにあるはずだけど？　Commitの自動化は完成しているけどそこに繋がっていないっていうことかな**

## 2. ★★実測（★私が 源で 直接 確かめた・2026-08-14 02:4x）

```
★★`twoder/autonomous_git.py` ＝ ★★★2026-07-23 作成（★3週間前）／ 4,781 bytes

★持っている物（★逐語・関数名と docstring）:
   ★`propose_commit(repo, changed_files, message, branch)`
      = 逐語『★Build a commit PROPOSAL (what WOULD be committed) without committing.
              ★Classifies files into autonomous-eligible (ledger) vs code (human-only)』
   ★`commit_gate(proposal, approval_token, ts, enabled)`
      = 逐語『★Requires: policy enabled AND within autonomous scope』
   ★`execute_commit(proposal, approval_token, ts, enabled)`
   ★`is_ledger_path(path)` ＋ `_LEDGER_MARKERS`
      = ★★台帳/登記は 自動可 ／ ★コード・docs は 人が要る、の 線引きが ★★既に 実装済み

★★★本番の 呼び手 = ★★0件（★呼んでいるのは `twoder/regression/test_autonomous_git.py` だけ）
★★★既定 = ★`AUTONOMOUS_GIT_ENABLED = False`（L15）
   ★逐語コメント =『★POLICY: commit=Taka. ★Enabling requires a recorded Taka policy decision (DE + CHG).』
```

## 3. ★★∴ 言い方を 直す

```
★誤 = 『★commit の 口が 無い ∴ Taka 裁定待ち』
★★正 = ★★★口は 在る ／ ★誰も 繋いでいない ／ ★★既定で 切ってある
        ＝ ★Taka に 要るのは ★『作ってよいか』では なく ★★★『切ってある物を 入れるか』の 1判断。
```

**★★★これは 本日 何度も 出た型（★在るのに 使っていない）の また1件。**
**★★★しかも ★`autonomous_git` は ★★今夜 我々自身が 数えた『誰にも呼ばれない部品 35本』の 中に 名前が 出ていた。**
**★★目の前の 一覧に 在ったのに ★『口が 無い』と 書いた ＝ ★★[[absence-reads-as-compliance]] そのもの。**

## 4. ★★お願い（★1つ・★新しい物を 作らない）

```
★★★`autonomous_git` を ★新規に 設計し直さない（★★3週間前の 実装を 読む）
★★Taka へ 上げる時は ★★『口が 無い』と 書かない ＝ ★★★『既定 False を 入れるか』で 上げる
★★★併せて 出す物 = ★★(a)いま 人（MGR）が 手で commit している 件数（★本日 実測できる）
                    ★(b)そのうち ★台帳/登記だけの commit は 何件か（★★自動可の 範囲に 入る分）
   ―― ★★★これが 無いと ★『入れたら 何回 減るのか』が Taka に 分からない。
```

## 5. ★★受入（★数で・★案）

```
★① ★★`autonomous_git` の 本番の 呼び手（★いま 0）
★★② ★人が 手で commit した 回数 ／ ★そのうち 台帳だけの 回数（★母数つき）
★★③ ★★`AUTONOMOUS_GIT_ENABLED` の 値と ★それを 変えた 記録（★★人の記憶に 置かない）
★★④ ★★コードの commit が ★自動側に 入っていない事（★★線引きが 効いている 実物1件）
★⑤ ★新台帳0 ／ ★口 0増 ／ ★新しい file 0（★★既存を 繋ぐだけ）
```

## 6. ★注意

```
★★[[in-the-machine-or-delete-it]]: ★3週間 切ったままの スイッチは ★★入れるか 捨てるか。★中間で 置かない。
★★[[claude-is-a-vendor-2der-calls]]: ★commit を 人が 押し続ける限り ★★Claude は 減らない。
★★★但し ★『commit=Taka』は ★Taka の 方針 ∴ ★★我々が 勝手に 入れない（★★上げるだけ）。
★★本線は ★経路表（EVO-0058）＝ ★別 item を 立てない。
```
