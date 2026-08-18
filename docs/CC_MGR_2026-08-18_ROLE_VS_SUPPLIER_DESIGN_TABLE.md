# 宛: 設計 / 監査 ―― 役名と供給主体の設計表（最小変更案のみ・実装していない）

## 0. 欠陥の言い直し（Taka 裁定）

> **`actor_role` の名前を、そのまま人間/機械の判定に使っていること。**

`MANAGER` を一律に白名簿へ足す案は**採らない**。

## 1. 設計表（_MAP 9状態・すべて実測から）

| operation | actor_role | `_machine_registry()` に在るか | `_MAP.claude_barrier` | `decide_rearm` の扱い | **実測の供給主体**（今夜の走行記録） |
|---|---|---|---|---|---|
| PLAN | MANAGER | **✓** | **True** | **人**（HUMAN_BARRIER） | **★機械**（5件とも CREATED を抜けた） |
| GENERATE | CODING_WORKER | ✓ | False | 機械 | 機械（QWEN_LIVECODER） |
| AUDIT | INDEPENDENT_AUDITOR | ✓ | False | 機械 | 機械（QWEN_AUDITOR） |
| DISPOSE | MANAGER | **✓** | **True** | **人** | **★機械**（止1/止0 の工程列に `DISPOSE` が在る） |
| REGENERATE | CODING_WORKER | ✓ | False | 機械 | 機械（止1 の列に在る） |
| UPPER_REVIEW | CLAUDE_SENIOR | **✓** | **False** | **人** | **★機械**（identity=`claude-senior` が自動で走行） |
| NONE (COMPLETE) | - | ✗ | False | 人 | 供給なし |
| BLOCKED | - | ✗ | True | 人 | 供給なし |

**3つの権威が食い違っている。**

```
登記簿        5役すべてを 機械として 登録（MANAGER・CLAUDE_SENIOR を含む）
_MAP          PLAN と DISPOSE を claude_barrier=True（関門）
              UPPER_REVIEW は False（機械でよい）
decide_rearm  MANAGER と CLAUDE_SENIOR を 人扱い（★_MAP より 厳しい）
実測          ★PLAN も DISPOSE も UPPER_REVIEW も 機械が供している
```

**`decide_rearm` は `_MAP` より厳しく、`_MAP` は実測より厳しい。** 3層でずれている。

## 2. PLAN / MANAGER ―― 役名と実主体が一致しない実例

- `_MAP`: `CREATED → ('PLAN','MANAGER',...,claude_barrier=True)`
- 登記簿: `MANAGER` **在り** ／ `BUILD_PLANNER` **在り**
- 実測: 今夜の5件すべてが `CREATED` を機械の走行で抜けた
- `manager_v0._machine_turn` の逐語コメント（過去の実測）:
  「`CREATED` の役は MANAGER/CLAUDE だが **入口は Qwen の planner で自動で供する**＝実測で進んでいた」

**∴ 役名 `MANAGER` は「人が供する」を意味しない。**

## 3. 最小設計案（実装していない・裁定待ち）

### 案の骨子

`decide_rearm` の第3引数を **`role`（文字列）から `machine_suppliable`（真偽）へ変える。**
判定器は役名を**知らなくなる**。

```
現在  decide_rearm(gate_exists, blocked, role: str,               findings_count)
       → role not in ('CODING_WORKER','INDEPENDENT_AUDITOR') なら HUMAN_BARRIER

案    decide_rearm(gate_exists, blocked, machine_suppliable: bool, findings_count)
       → machine_suppliable が偽なら HUMAN_BARRIER
```

**`machine_suppliable` を作るのは呼び手（front door）。** 材料は**既存**のものだけ:

```
machine_suppliable = (登記簿に その actor_role の 供給者が 在る)
                     AND (operation が NONE でも BLOCKED でもない)
                     AND (★権限境界が 別に 許している)
```

### 条件を満たしているか

| Taka の条件 | 満たし方 |
|---|---|
| MANAGER 全体を自動許可しない | **役名で許可しない。** 許可の根拠は「その操作を供給できる者が登記簿に在るか」＋第3項の権限境界 |
| CLAUDE_SENIOR 等の安全境界を緩めない | **第3項を独立に置く。** 登記簿に在っても権限境界が否と言えば偽 |
| HUMAN_BARRIER を削除しない | **語は残す。** 返る条件が「役名」から「供給可能性」へ変わるだけ |
| 今回の2 task を再試行しない | していない |
| 22/33 へ広げない | していない |

### ★残る政策の問い（私は決めない）

**第3項「権限境界」を何で表すか。** 候補は `_MAP.claude_barrier`。
ただし**それを採ると `PLAN` と `DISPOSE` は引き続き `HUMAN_BARRIER`** になり、
**今回の2 task は塞がれたまま**。実測（機械が供している）とも食い違ったまま。

```
選択肢α  権限境界 = _MAP.claude_barrier をそのまま使う
          → 安全は最も堅い ／ ★PLAN が機械供給される実態と _MAP のずれは 残る
選択肢β  _MAP の claude_barrier を 実測に合わせて 直す（PLAN を False へ）
          → 実態と一致 ／ ★正本を変える＝上申条件①③に当たる
```

**私は決めない。** どちらも「安全境界を緩める」可能性を持ち、Taka の価値判断が要る。

### 実装の作法

`decide_rearm` は **2DER 製の純関数**。**MGR は書き換えない。**
変えるなら**契約経路で作り直す**（引数の意味が変わるので新しい部品名にする）。

## 4. 失われた観測（推測で埋めない）

**あの2 task で「初回 PLAN がなぜ進まなかったか」は現在の記録に無い。**
front door は planner の失敗理由を応答に載せる（`webui` の逐語 Build 10(S3)）が、
**MGR の走行スクリプトが状態だけ印字して捨てた。**

**★別の観測欠陥として残す** ―― 「front door が返した拒否・失敗の理由が、
呼び手の手元にしか無く、後から task で引けない」。

## 5. 4つを別々に扱うべきか ―― **★全部 別に扱うべき**

| 概念 | 現在の持ち主 | 別扱いが要る理由（今夜の実証） |
|---|---|---|
| **役名** | `_MAP[state][1]` | `MANAGER` が 人と機械の両方を指している。**名前は主体を決めない** |
| **次操作** | `_MAP[state][0]` | `COMPLETE→NONE` を「機械の番」と誤分類した（R6 で実際に踏み、4語へ直した） |
| **実際の供給主体** | `_machine_registry()` | **登記簿は 5役**。役名の白名簿(2)とずれ、`_MAP` の関門(True/False)ともずれる |
| **権限境界** | `_MAP.claude_barrier` ／ `taka_authority` ／ 門の `runnable` | `decide_rearm` が **これを役名で代用**したのが今回の欠陥そのもの |

**4つを1つの欄で代用した瞬間に、今回の障害が起きた。**
General Manager は **4欄を別々に出す**べきで、**混ぜた欄を作ってはいけない。**

## 6. していないこと

修正 0 ／ 白名簿の変更 0 ／ 再試行 0 ／ R6 への権限門欄追加 0 ／ 22・33 へ拡大 0。
**EVO-0019 v1 は停止のまま。**
