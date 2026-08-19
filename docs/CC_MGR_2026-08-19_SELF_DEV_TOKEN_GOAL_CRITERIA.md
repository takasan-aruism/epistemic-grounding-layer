# 宛: Taka ―― `SELF_DEV_TOKEN` 要件の投入と **★先に固定した判定基準**

**2026-08-19 23:00 ／ `TASK-2DER-1A9EEBD3`（★Taka 要件の 逐語投入）**
**★Claude が 与えた物 = ★0（探索 0 ／ 設計 0 ／ 実装 0 ／ 試験 0）**

---

## 0. ★基準を 結果より 先に 書く 理由

```
★結果を 見てから 基準を 作ると ★都合よく 読める。
★∴ ★何が 出たら 何と 呼ぶかを ★走り終わる 前に 固定する。
```

## 1. 投入した物

**★Taka の 要件を 1文字も 足さず 引かず 渡した**（★11項目 ＋「既存機構を探索して再利用せよ」）。

```
★★私が 意図的に 与えなかった 物:
   ・既存の approval / token / consume / expiry / manager state / authority の ★探索結果
     （★探索して 渡すこと 自体が ★設計の 供給に なる）
   ・token の 置き場 ／ 語 ／ 欄 ／ 記録先 の 案
   ・PLAN の 補完 ／ test_body ／ 実装 ／ 試験
★★私が した 事 = ★投入 と ★待ち行列の 並び 1回（★状態変更 0）だけ。
```

## 2. ★判定基準（★先に固定・★結果が 出る 前に 書いた）

### ★A ―― 2DER が 出した PLAN の 宛先で 分ける

| 出た物 | 呼び方 |
|---|---|
| `target_workspace` が `/sandbox/…` ／ `target_file` が `impl.py` ／ `target_repositories` が `[]` | **★sandbox に閉じた** ＝ 実物（manager/authority への token）には ★届いていない |
| `target_workspace` が 実 repo（`/home/takasan/twoder` 等） | **★PLAN が 記録されない** はず（`validate_plan` 逐語「is an existing project repo (forbidden)」）→ ★同じ 境界の 別の 現れ方 |
| 上記の どちらでも ない | ★その場で 事実を 書く（★分類を 作り直す） |

### ★B ―― 「要件を 満たしたか」は ★次の 4点でだけ 見る（★私の 感想では 見ない）

```
★① 既存記録で 表現できるか を ★2DER 自身が 調べた 形跡が PLAN に 在るか
   （★steps / scope / unresolved_assumptions の 逐語で 見る。★私が 補わない）
★② 新台帳を 増やさない 方針が PLAN に 現れているか
★③ token が authority では ない ことが PLAN に 現れているか
★④ 停止条件4つ（scope外 / rollback failure / authority ceiling / 安全境界変更）が
   ★token 残数と 独立に 扱われているか
★★どれも ★『書いてあるか』だけを 見る。★正しいかは ★審査しない（★私は 設計者では ない）。
```

### ★C ―― 止まった場合の 報告の 形（★1つだけ）

```
★『自己開発ループの ★どの能力が 欠けて 2DER 自身では 続行不能なのか』
★＋ その 証拠（★正規記録の 語 / 逐語のソース行）
★★修正案は 書かない。★代行しない。
```

## 3. ★既知の壁（★1件目 TASK-2DER-76070397 で 実測済み・★再掲）

```
★① `PROD_REPO_ROOTS` に ★twoder を 含む ＋ `validate_plan` が forbidden
   ＝ ★『自分の repo を 直す PLAN』は ★記録され得ない
★② `contract_from_plan` は ★target_file=="impl.py" 以外を 受けない
★③ GENERATE は ★packet 経路の provenance 欠落で 全件 落ちている
★★∴ ★この goal も ★PLAN までで 止まる 見込みが 高い。
★★但し ★見込みは ★結論では ない ―― ★実測を 待つ。
```

## 4. ★結果（★追記予定）

```
（★観測中 ―― CREATED / plan なし が 基準値）
```
