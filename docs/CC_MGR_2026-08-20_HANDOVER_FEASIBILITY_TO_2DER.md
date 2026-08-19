# 宛: Taka ―― **ここから 2DER だけで 進めるか（★実測・★実装 0・★投入 0・★許可リスト 未変更）**

**2026-08-20 ／ `twoder@4a7a033` ／ `ALLOWED_TARGET_FILES = ("impl.py",)` の まま**
**★SELF_DEV_TOKEN = ★5/5**

---

## ① ★★2DER 自身が `allowed_target_files.py` を 変えて 2件目を 足せる 正規経路は ★★存在しない

**★経路を 1段ずつ 引きました。★切れている 所を ★★呼び手の 数で 示します。**

| 段 | 実測 | 通れるか |
|---|---|---|
| **生成の 対象名** | `ALLOWED_TARGET_FILES = ("impl.py",)` | ★★名乗れない（★自分を 許可リストに 載せないと 自分を 直せない＝循環） |
| **作業場** | `build_planner:68` の `PROD_REPO_ROOTS` に ★`/home/takasan/twoder` が 入っている。`:319` で PLAN が 落ちる（逐語「target_workspace … is an existing project repo (forbidden)」） | ★★実 repo を 作業場に できない（★これは 設計どおり） |
| **成果物** | GENERATE の 成果物 = ★**全文 source（文字列）** | ― |
| **全文 → 差分** | ★repo 本体に ★差分を **作る** 物が ★★0件（`difflib` = 0 ／ `generate_unified_diff` = 0） | ★★★切れている |
| **差分 → artifact** | `patch_bridge.worker_output_to_artifact(worker_diff, files_changed, base_commit)` ★本線の 呼び手 = ★★0（regression のみ） | ★★切れている |
| **artifact → 適用** | `apply_cycle(...)` ★呼び手 = ★★0（★どこにも 無い） | ★★切れている |
| **通電（実 repo）** | `patch_bridge._mint_test_energize` は 逐語「★There is NO real-repo minter here」＝ ★throwaway 限定・実 repo は 拒否。実 repo 用は `bridge_minter.mint_real_energize` のみ ★本線の 呼び手 = ★★0 | ★★切れている |
| **通電の 門** | `bridge_minter` gate(2) = `authority_owner=='TAKA'` かつ `granted_by=='TAKA'`、★self-/model-authored は 拒否 | ★★通らない ―― **但し これは 欠陥では なく 安全境界** |

```
★★＝ ★2DER の 成果は sandbox で 止まる。★実 repo へ 出る 口は ★1つも 繋がっていない。
```

**★「当てる」側は 既に 在り、★2DER が 書き、★既に 配線済み です（★念のため）:**

```
twoder/apply_unified_diff.py  … ★2DER が 契約経路で 書いた（`patch_bridge:133` が 呼んで いる）
★★＝ ★差分を 当てる 側は ★在る。★★無いのは 差分を 作る 側 だけ。
```

---

## ② ★経路が 無い ∴ 「その 経路で 完全移管」は ★該当なし

**★1点だけ ★言葉の 確認を させて ください。**

```
★仮に 全部 繋がった と しても ―― ★`bridge_minter` の gate(2) は 残ります。
★★＝ ★実 repo へ 書く たびに ★Taka の ENERGIZATION_ADJUDICATION が 要る。
★★＝ ★「2DER が 誰にも 断らず 実 repo を 書く」形には ★★設計上 なりません。
★★∴ ★私が 言う「移管できる」は ★「2DER が 経路を 自力で 回し、★門で Taka に 上げる」形 まで です。
★★この 門は ★外すべきでは ないと 考えます（★自己通電の 禁止＝2DER の 骨格）。
```

---

## ③ ★★最後に 必要な bootstrap は ★1つ

```
★★「2DER が 生成した 全文 source を、★実 repo の 相対 path を 宛先と する
   unified diff の artifact に 変換し、★既存の `apply_cycle` を 1回 呼ぶ」
   ―― ★その ★1本の 接続 を ★repo に 置く こと。
```

**★なぜ これ 1つで 足りるか:**

```
★宛先（どの file を 書くか）は ★既に patch 層が 持っている
   ―― `worker_output_to_artifact(worker_diff, ★files_changed, base_commit)` の
      `files_changed[0]` が ★そのまま `--- a/<path>` `+++ b/<path>` に なる（逐語）。
★★∴ ★「生成の 対象名が impl.py 固定」は ★★この 接続が 在れば 障害に なりません
   （★sandbox では impl.py の まま 作り、★宛先は 接続が 渡す）。
★当てる／dry-run／rollback／reconciler／単一file／allowed_files 検査 は ★すべて 既に 在る。
★★∴ ★足りないのは ★『作る 1段』と『呼ぶ 1本』だけ。
```

**★なぜ 2DER 自身では できないか（★前回と 同じ 型）:**

```
★その 接続は ★`twoder` repo の 中の file です。
★2DER が repo に file を 置く 唯一の 経路が ★★まさに その 接続 です。
★★＝ ★自己参照。★2DER は 自分を 繋ぐ 線を 自分では 置けません。
```

**★★重要 ―― ★中身は ★既に 在るかも しれません:**

```
★`twoder/runs/received/TASK-2DER-FD9975C9.py` が ★`difflib` を 使って います。
★★但し ―― ★私は 中身を 読めません（★実行結果の 横読みは 禁止・★フックが 実際に 拒否した）。
★★∴ ★「新しく 書かせる」前に ★★2DER に 聞くべきです
   ―― ★過去に 作った 差分生成の 成果が ★そのまま 使えるか。
★★＝ ★bootstrap は「★書く」では なく「★★既に 在る 物を 置く」で 済む 可能性が あります。
```

---

## ④ ★私の 上申（★実装は していません）

```
★上申の 型 = ★「新しい 設計判断」＋「安全境界に 触れる 可能性」。
★★お伺いしたいのは 2点だけ です:

 (1) ★上の ★1本の 接続 を ★最後の bootstrap と して 認めるか。
 (2) ★認める 場合、★中身を ★★2DER に 聞いて から に するか
     （★`FD9975C9` の 既存成果が 使えるなら ★私が 書く 行は ★0 に できます）。

★★私は (2) を 先に する ことを 推します。★理由 = ★私が 書く 量が 減る 方に 倒れる ため。
★★どちらも ★front door への 投入が 要ります が ―― ★投入は ★今回 していません（★ご指示どおり）。
```

## ⑤ ★していないこと

```
★実装 0 ／ ★許可リスト 未変更（("impl.py",) の まま）／ ★front door への 新規 goal 投入 0
★repo 変更 0（★`twoder` HEAD = `4a7a033` 不変）／ ★常駐 停止の まま
★台帳の 直読 0（★`runs/` は フックが 拒否＝★境界どおり）／ ★状態を 進めた task 0
★SELF_DEV_TOKEN = ★5/5
```
