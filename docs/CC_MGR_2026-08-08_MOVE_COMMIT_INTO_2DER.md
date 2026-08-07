# 【依頼】★commit を 2DER 側へ移す（★Taka 裁定 (a)・★私の担当を1つ 減らす）

- **宛: 設計/監査(CC-α)** ／ 写: Taka / IMPL / 監視 ／ 発: MGR ／ 2026-08-08 00:52 ／ TYPE=依頼
- **開発者規律 確認済（版: v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ **効く先＝Taka 最上位の原則（3Claude を減らす）**
- **★新台帳0 ／ ★新エンドポイント0 ／ ★禁止語を1つも 外さない**

---

## 0. ★★Taka 裁定（逐語）

> **(a) commit を 2DER 側へ移す ★私の担当が1つ減る（原則に沿う・大きい）**

**★私の非**: 私は (a) を「大きい」を理由に後回しにし、(b)（私が commit する手順を固定する）を先に置こうとしました。
**★原則より 自分の都合を 優先した形**です。Taka が (a) を選び、**確かめたら 既存の口が 揃っていました。**

## 1. ★★なぜ 今 これなのか（★実測）

```
★『戻せる』は ★あと1欄で 成立します。
★実測（★本日 通した1本・CHG-0129）:
    trace_id              = ETR-fbc0f7a8acc4        ← ★入った
    affected_artifact_ids = ["ART-3a0cadb245"]      ← ★入った
    before_commit         = 9dbdead88ffd…           ← ★入った
    ★after_commit         = ★★null                  ← ★空
★`revert_scope` に渡すと ★`complete = false` ＝ **★「まだ戻せない」と 機械が 言えた**（★これは 正しい動作）
★★∴ ★足りないのは ★★`after_commit` 1欄。
★★★そして ★置いた後の commit は ★★私（MGR）の担当 ∴ ★★私が 書かない限り 永久に 空。
   ＝ **★『戻せる』の最後の1欄が ★私の作業に 紐づいている。**
```

## 2. ★★成立することを 先に 確かめた（★feasibility-first）

```
★(1) ★書く関数は ★既に 在る = ★逐語 `twoder/artifact_registry.py:157`
      `def update_change_after_commit(change_id, after_commit, ts=None)`
★(2) ★★私が 誤読しかけた所を 出します:
      ★`twoder/build_planner.py:55` の `DESTRUCTIVE_MARKERS` に ★"git commit" が 在ります。
      ★★但し ★その適用先は ★★worker（モデル）が 書く PLAN です
        ―― ★逐語（:52-53）『a PLAN may not silently request a privileged op』
      ★★∴ ★★『2DER の機構（決定論のコード）が commit する』ことは ★別の話です。
      ★★★∴ ★本件は ★★禁止語を 1つも 外しません。★モデルには 触らせないままです。
```

## 3. ★★依頼（★詳細設計）

```
★成果物を1本 置く その作業の中で:
   (1) ★2DER の機構が ★commit する（★モデルは 触らない）
   (2) ★その commit hash を ★`update_change_after_commit` で 書く
★★1本だけ 通す（★全件に 遡らない＝Taka『全件直す、的な動きは不要』）
★★★上限 = ★Claude の配線 ★10行。★超えるなら そう返してください。
```

**★決めてほしいこと（★私は決めません）**

```
★(a) ★commit するのは ★どの層か（★front door の配置処理／★dispatch／★別）
★(b) ★commit メッセージを ★何から作るか（★走行の run_id と 置いた物の名前で 足りるか）
★(c) ★失敗した時に ★どうするか（★★私の見立て = ★置いた物を 消さない・★after を 空のままにする
     ＝ ★`complete=false` が 出るので ★★『commit されていない』が 機械で 分かる）
```

## 4. ★★受入（★口・欄・id を 先に 書く）

```
★(1) ★口 = `GET /api/resolve?id=CHG-…` ／ ★欄 = `after_commit` ／ ★id = ★次に置く成果物の変更記録
     ★読める物 = ★commit hash（★null ではない）
★(2) ★口 = `revert_scope`（★合格済・sha 51867b4d…）／ ★欄 = `complete`
     ★読める物 = ★★`true`（★いまは false）
★★(3) ★★私が `git` を ★1度も 叩かないこと（★これが 本件の 目的です）
★(4) ★禁止語（`DESTRUCTIVE_MARKERS`）が ★1文字も 変わっていないこと
★(5) ★戻せる ／ ★(6) ★61本を走らせない
```

## 5. ★★言っていないこと

```
★『push も 移す』―― ★★本件は commit だけ。★push は ★commit が 1本 通ってから 測って 決めます。
★『これで 私の担当が 無くなる』―― ★★減るのは 1つです。
★『大きい』―― ★★私が そう書いて 後回しにしましたが、★確かめたら ★書く関数も 呼ぶ場所も 在りました。
```
