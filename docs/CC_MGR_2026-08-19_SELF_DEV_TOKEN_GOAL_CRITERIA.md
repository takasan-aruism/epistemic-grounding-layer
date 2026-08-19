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

## 4. ★★結果 ―― **PLAN は 成立。★実装は 1バイトも 出ていない**

```
★記録の 並び = CREATE → PROCESS_EVENT → ★PLAN → GENERATE → AUDIT → DISPOSE
              → UPPER_REVIEW(FAIL) → REGENERATE → AUDIT → DISPOSE → UPPER_REVIEW(FAIL)
★PLAN identity = 2der-qwen-build-planner
★GENERATE / REGENERATE = ★どちらも reason="no provenance supplied (hand-authored packet / bypass)"
   runner_exit=null ／ artifact_sha256="" ／ diff=0B ＝ ★runner は 一度も 動いていない
```

### ★基準A（宛先）の 判定 → **★sandbox に閉じた**

```
target_workspace   = ★"./sandbox/workspace"
target_file        = ★"impl.py"
target_repositories= ★[]        allowed_files = ["impl.py","test_impl.py"]
★★＝ `manager_v0` にも `authority` にも 届いていない。
★★＝ 作ろうとしたのは ★sandbox 内の 単独クラス（逐語 requirement:
   「Implement a ★SelfDevBudget class that manages a SELF_DEV_TOKEN starting at 5 …」）
```

### ★基準B（4点・★書いてあるかだけ）の 判定

| # | 見る物 | 結果（★逐語） |
|---|---|---|
| ① 既存記録で表現できるか調べた形跡 | steps | **★書かれている**「Explore existing approval/token/consume/expiry/manager state/authority mechanisms.」 |
| ② 新台帳を増やさない | prohibited_actions | **★書かれている**「Create new ledgers.」（★禁止として） |
| ③ token は authority ではない | prohibited_actions ／ authority_requirements | **★書かれている**「Use token as authority.」（★禁止）／ `authority_requirements = []` |
| ④ 停止条件4つが token 残数と独立 | requirement ／ steps | **★書かれている**「enforce hard stops for scope out, rollback failure, authority ceiling exceed, and safety boundary change ★regardless…」／「Integrate stop conditions for scope, rollback, authority, safety.」 |

**★★4点とも ★文面には 現れた。★正しいかは 審査しない（★私は 設計者では ない）。**

### ★★但し ―― **「探索した」ことに ★なっていない**

```
★`unresolved_assumptions`（★逐語・★2DER 自身が 書いた）:
   「Existing records format is ★assumed to be JSON for simplicity, but adaptable.」
   「Taka approval mechanism is ★assumed to be a function call or flag.」
★★＝ ★既存機構を 調べた 結果では なく ★仮定 を 置いている。
★理由（★構造）= 「Explore …」は ★PLAN の 中の ★手順 に 過ぎず、
   ★それを 実行する 段（GENERATE / runner）が ★一度も 動いていない
   ＝ ★★探索は ★1回も 行われていない。
★★∴ Taka の「まず既存機構を探索して再利用せよ」は ★PLAN 段では 満たせない
   （★探索は 実装段の 仕事に なっている）。
```

## 5. ★★続行不能の理由（★欠けている能力・★証拠付き）

```
★★① 実 repo を 宛先に できない（★1件目と 同じ・★再現）
   証拠 = 実測 PLAN の target_workspace="./sandbox/workspace" ／ target_repositories=[]
        ＋ `build_planner.PROD_REPO_ROOTS` に twoder を 含む
        ＋ `validate_plan` 逐語「target_workspace %r is an existing project repo (forbidden)」
   ＝ ★`SELF_DEV_TOKEN` を ★実物の manager/authority に 持たせる PLAN は ★記録され得ない。

★★② GENERATE が 動かない（★1件目と 同じ・★再現）
   証拠 = GENERATE/REGENERATE とも reason="no provenance supplied" ／ runner_exit=null
   ＝ ★sandbox の おもちゃさえ 作れない ＝ ★試験も 走らない。

★★③ 探索が 実装段に 置かれている
   証拠 = steps に「Explore …」／ unresolved_assumptions に「assumed …」×2
   ＝ ★②が 直らない 限り ★探索も 永久に 行われない（★①②に 従属）。
```

**★★最小の 1手は ★②（provenance）―― ★①より 先。**
理由: ②が 直れば ★sandbox 内でだけでも ★探索・実装・試験が 回り始める。
①は ★安全境界の 変更 ∴ ★Taka の 判断が 要る。

## 6. ★上申（★Taka 予告どおり ―― ★ここだけ）

```
★★実 repo（`/home/takasan/twoder` 等）を PLAN の 宛先に 許すか。
★現状 = `PROD_REPO_ROOTS` で 全面禁止 ＝ ★2DER は 自分を 変更できない。
★★これを 変える ことは ★安全境界の 変更 ∴ ★私は 触っていません。
★★代替（★私の 決定では ない・★材料）= ②だけを 先に 通し、
   ★repo 反映は 既存の patch 一式（`patch_bridge` / `bridge_minter` / `apply_cycle`）に
   任せる 形も 在り得る（★但し `patch_bridge` は 逐語「There is NO real-repo minter here;
   that is a §3 design + Taka gate」＝ ★同じ 門に 戻る）。
```

## 7. していないこと

```
★探索 0 ／ 設計 0 ／ 実装 0 ／ 試験 0 ／ 契約 0 ／ skeleton 0 ／ test_body 0
★run_next 0 ／ task 手動前進 0 ／ 状態変更 0 ／ 修正案 0
★手を出したのは ★待ち行列の 並び 1回だけ
```
