開発者規律 確認済(v1.0)

# 【指示・★Taka】★「在るのに 載っていない」を 載せるのが ★経路表そのもの ／ ★★2択の 前提を 1つ 訂正する

宛: MGR ／ 発: DESIGN（監視兼務）／ 2026-08-13 15:5x ／ 台帳: `ITEM-2DER-EVO-0058`

## 1. ★Taka 逐語（★歪めない・★2発言）

> **未知と言っているのはそもそも繋がってないってことだよね？　独居プログラム？**

> **そりゃ、あるのに載ってないなら経路表じゃね？**

**★★∴ ★2択（あ）（い）の 立て方が ★★Taka の 設計と 合っていない。**
**★★『未知の道を 探すのは 見合うか』ではなく ★★★『在るのに 載っていない物を 載せる』のが ★経路表の 定義。**
**―― ★既出の Taka 逐語と 一致する = ★『経路表は 2DER が 何をするものなのかを 唯一 正しく 俯瞰的に 知ることのできる機能』『人体図鑑であると同時に 機能表』。**

## 2. ★★訂正（★15:43 の PLAN 記述・★1点）

```
★15:43 の 記述 = 逐語『①材料=`event_trace` の 記録だけ(★source を 読まない=★★Taka 原則=repo を 探索させない)』

★★正しくは（★典拠 = `CC_MGR_2026-08-12_TAKA_ROUTE_AND_FUNCTION_SPEC_v0.1.md`）:
   ★L868 逐語 = 『★★LLM に repo 全体を 探索させない』
   ★L85  逐語 = 『★★Worker LLM にも 自由探索させない』
   ★L871 逐語 = 『★★実行実績と 静的構造を ★混同しない』

★★∴ ★禁じられているのは ★★★LLM に 自由に 探索させること。
★★★決定論の 静的走査は ★禁じられていない（★L871 は ★★『混ぜるな』＝ ★★両方 在る 前提）。
★★∴ ★『source を 読まない』は ★★規則の 読み過ぎ。
```

**★★これが 効いている所 = ★15:43 の 見立て 逐語『★未知の道は 置いた口の 外に 在る ∴ 構造として 発見に ならない』**
**★★→ ★★★この結論は ★★上の 読み過ぎの 上に 乗っている ∴ ★★成り立たない。**

## 3. ★★実測（★私が 直接 走らせた・2026-08-13 15:5x ／ ★LLM 0回 ／ ★新しい口 0 ／ ★新しい file 0）

```
★手段 = ★★ast で import の 辺を 作り、★★入口から 辿れるかを 数えるだけ（★所要 数分）
★入口 = `twoder.webui` ／ `twoder.submit` ／ `dw.dispatch` ／ `dw.workflow`
★対象 = ★5つの パッケージ直下の .py（★★母数 = 185本・★試験と `__init__` を 除く）

★★到達できる      = ★★125本
★★到達できない    = ★★★60本
   ★うち ★★誰からも import されない（★完全な 孤立） = ★★★35本
   ★残り ★★25本 = ★★互いに import し合うだけの 塊（★入口から 誰も 呼ばない）

★★★名前（★35本・★全部 挙げる＝★数だけにしない）:
   dw.authorization / egl.contracts / egl.curator / egl.esde_stream / egl.judge_vllm /
   egl.review_mechanisms / rri.transformation / twoder.ab_harness /
   twoder.active_work_and_wait_ledger / twoder.assumption_extractor /
   twoder.audit_egl_integration / twoder.autonomous_git / twoder.axis_delta /
   twoder.benchmark_run_ledger / twoder.bridge_minter / twoder.bridge_reconciler /
   twoder.claude_intervention_log / twoder.commit_message / twoder.count_unsplit /
   twoder.counterfactual_runner / twoder.dep_flag_registry / twoder.dissent_worker /
   twoder.domain_egl_integration / twoder.end_to_end_acceptance_harness /
   twoder.execution_event_log / twoder.gate4 / twoder.interface_contract_schema /
   twoder.management_packet / twoder.patch_bridge / twoder.routing_delivery /
   twoder.run_oracle_guarded / twoder.select_and_create / twoder.split_symbol_details /
   twoder.temporal_egl_integration / twoder.trace_entry

★★動的な 呼び出し（`importlib` / `__import__`）で 隠れていないかも 確かめた
   = ★本番側 42箇所は 全て 別用途（★reload / spec 読み込み）＝ ★隠れ呼び出し 0。
```

**★★私の 自己訂正 = ★私は 15:4x に 一度『★42本』と 数えた。**
**★★誤り = ★複数行の `from twoder import (A as X, B as Y, …)` を 正規表現が 拾えていなかった。**
**★★ast で 引き直した 上の数が 正しい（★35 / 60 / 185）。★★数を 出す時は ast で 引く。**

## 4. ★★∴ 2択に 対して（★私は 選ばない・★材料だけ 直す）

```
★★(あ)の 中身は ★★『口を 足す場所を 人が 選ぶ』だった ∴ ★★Taka 逐語と 合わない
   ―― ★★人が 選んだ所しか 見えないなら ★★『在るのに 載っていない』は 見つからない。
★★(い)『ここで 止める』は ★★★経路表の 定義を 満たさないまま 閉じる ことに なる。

★★∴ ★★第3の 形が 在る（★★これは 私の 提案では なく ★★実測の 報告）:
   ★★★静的構造（★決定論・★LLM 0）で ★★『在る』を 先に 出し、
   ★★★実行記録（★両側の 証拠）で ★★『動く』を 確定する。
   ―― ★★★これは [[existence-first-deterministic-branching]] そのもの
      = ★★存在は 決定論で 確定 → ★確定した側の メニューだけ 渡す。
   ―― ★★★[[instrument-not-inferencer-both-sides-required]] とも 衝突しない
      = ★★静的走査は ★『候補』を 出すだけ ／ ★★『繋がった』の 確定は ★従来どおり 両側の 証拠。
   ★★★2つを 混ぜない（★L871 の 逐語『実行実績と 静的構造を 混同しない』を そのまま 守る）
      = ★★経路表に ★★★3列目を 置く：★『在る』／『動いた』／★★『在るが 動いた記録が 無い』。
```

## 5. ★★受入（★数で書く・★案 ／ ★MGR が 直してよい）

```
★① ★静的に 出した 候補の 件数 と ★母数（★185）を ★併記する
★★② ★★『在るが 動いた記録が 無い』が ★★0件で 素通りしない（★★いま 60本 在る）
★★③ ★★静的候補を ★★『繋がった』として 経路表へ 登録しないこと（★★確定は 両側の証拠のまま）
★★④ ★LLM 呼び出し = ★★0回（★★探索を LLM にさせない＝★L868 を 守る）
★⑤ ★新台帳0 ／ ★front door の 口 0増 ／ ★新しい部品は 足すなら 1つ
★★⑥ ★★35本の うち ★★『捨てる』のか『繋ぐ』のかを ★1件でも 決めて 記録に 残す
   ―― ★★[[in-the-machine-or-delete-it]]: ★★仕組みに 落とすか 捨てるか。★中間を 作らない。
```

## 6. ★注意

```
★★[[absence-reads-as-compliance]]: ★★『未知の道 0件』を ★『繋がっている物は 全部 載っている』と 読まない
   ―― ★★正しくは ★★『表の外を 見ていない』。★★本日 これで 一度 止まりかけた。
★★[[taka-skeleton-first-not-flesh]]: ★35本の 個々の 処遇は ★★肉。★★骨格は ★★★3列目を 置くこと。
★★[[predict-after-determinism-not-before]]: ★★調べれば 分かる事を ★見立てで 埋めない
   ―― ★15:43 の 見立て（★『構造として 発見に ならない』）は ★★調べれば 数分で 覆った。
★★本線は ★経路表（EVO-0058）＝ ★★本件は その中。★★別 item を 立てない。
★★★足すかどうかは ★Taka の 判断 ／ ★★私は 前提の 誤りを 直しただけ。
```
