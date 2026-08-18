# 宛: 設計 / 監査 ―― 再武装判定の二重定義除去（最小案）＋ PLAN 権限境界の別調査

**実装していない。`_MAP` も `decide_rearm` も変更していない。**

## 1. 二重定義をどう除去するか

### いま（二重定義）

```
_machine_registry()   5役 ['CODING_WORKER','INDEPENDENT_AUDITOR','MANAGER','BUILD_PLANNER','CLAUDE_SENIOR']
decide_rearm          2役 ('CODING_WORKER','INDEPENDENT_AUDITOR')  ← ★手書きの部分集合
```

**同じ知識（誰が供給できるか）が 2箇所に別の形で在る。**

### 案（役名を判定器から取り上げる）

```
現在  decide_rearm(gate_exists, blocked, role: str,                findings_count)
案    decide_rearm(gate_exists, blocked, machine_suppliable: bool, findings_count)
```

`machine_suppliable` は**呼び手（front door）が既存の正本・登記簿だけから**作る。**新しい規則を作らない。**

```
machine_suppliable =
      (A) _machine_registry() に その actor_role の 供給者が 在る      ← 供給できるか
  AND (B) _MAP[state].operation が NONE でも BLOCKED でも ない        ← 次操作が 在るか
  AND (C) _MAP[state].claude_barrier が False                        ← 供給させてよいか
```

**(A) と (C) を分けるのが要。** 「機械が供給できる」と「機械に供給させてよい」を**別の材料**から取る。
登記簿に在るだけでは自動再武装しない。

### 呼び手の変更（front door・1箇所）

```python
# 現在
_v = _DR(gate_exists, blocked, str(_nlo0.get("actor_role")), undisposed)
# 案
_ok = (_nlo0["actor_role"] in _machine_registry()) \
      and _nlo0["operation"] not in ("NONE","BLOCKED") \
      and not _nlo0["claude_barrier"]
_v = _DR(gate_exists, blocked, _ok, undisposed)
```

**`decide_rearm` は 2DER 製の純関数。MGR は書き換えない。契約経路で作り直す。**

## 2. 既存の安全境界は維持されるか ―― **維持される**

| 境界 | いま | 案 |
|---|---|---|
| `MISSING_GATE`（門が無い） | 第1引数 | **不変** |
| `BLOCKED`（塞がれている） | 第2引数 | **不変** |
| 未処分 finding | 第4引数 `findings_count > 0` → `UNDISPOSED_FINDING` | **不変** |
| `NONE` / `BLOCKED` は不可 | 役名の白名簿で結果的に不可 | **(B) で明示的に不可** |
| `CLAUDE_SENIOR`（UPPER_REVIEW） | 役名で不可 | **(C) で判定**。`_MAP` は `claude_barrier=False` ★**ここは緩む** |
| `MANAGER`（PLAN / DISPOSE） | 役名で不可 | **(C) で不可のまま**（`claude_barrier=True`） |

### ★正直に言う ―― 1箇所だけ緩む

**`UPPER_REVIEW` は `_MAP` 上 `claude_barrier=False`** なので、案では**再武装が通る**。
現在は役名 `CLAUDE_SENIOR` で止めている。**「緩めない」という条件に抵触しうる。**

**選べる形は2つ。私は決めない。**

```
γ  (C) を _MAP.claude_barrier だけにする   → UPPER_REVIEW が 緩む（実測では機械が供している）
δ  (C) に 明示の 除外一覧を 足す           → ★新しい手書きの一覧＝二重定義が 別の場所へ移るだけ
```

**δ は今回直そうとしている病そのもの**なので、私は γ を推すが、**緩みが1箇所出ることを承知の上での裁定が要る。**

## 3. HUMAN_BARRIER の意味はどう変わるか

```
いま  「次操作の役名が、手書きの白名簿2つに無い」
案    「次操作を 機械が供給できない、または 供給させてよいと 正本が言っていない」
```

**語は残す。** 概念は「人の関門」のまま。**根拠が役名から正本へ移る。**

## 4. PLAN が止まる時、「供給不能」と「権限制約」を区別できるか

**★このままでは区別できない。** `machine_suppliable` は真偽1つで、(A)(B)(C) のどれで落ちたかが消える。
**それは今回直そうとしている「4つを1欄へ潰す」病の再発。**

**∴ 呼び手が 3つの事実を別々に記録すること を最小の付帯条件とする。**

```
拒否の記録に  registry_has: bool ／ operation: str ／ claude_barrier: bool  を そのまま 載せる
```

これで **「PLAN は供給者が居る（`registry_has=True`）が、正本が関門と言っている（`claude_barrier=True`）」**
と読める。**新しい欄を作らず、既に在る3つの値を捨てないだけ。**

## 5. PLAN の `claude_barrier=True` は現行正本として妥当か ―― **★古い制約の可能性が高い**

**時系列（git 履歴・実測）**

```
2026-07-11  2c183b5  claude_barrier が入る（★最初の dispatch ループ）
                     ★この時点で PLAN の機械供給者は 存在しない
2026-07-14  28fefa9  build_planner.py 初出
                     "Qwen BUILD_CAPABILITY ★PLAN actor + fail-closed validation"
2026-08-17  52a2f08  台帳「設計の実行主体を分解(★PLAN=Qwen・消去法)」
```

**`claude_barrier=True` は planner が存在しない時期に置かれ、3日後に機械供給者ができた。**
その後1ヶ月、**`_MAP` は更新されていない**（`claude_barrier` を含む commit は 07-11 の1件のみ）。

### 5つの問いへの答え

| 問い | 答え |
|---|---|
| ① いつ・なぜ入ったか | **2026-07-11・最初の dispatch ループ**。`F-E3 fix; EXEC-A infra revision` |
| ② planner より前の制約か | **★はい。** planner は 3日後（07-14） |
| ③ 今も安全上の理由が残るか | **未確定。** 07-11 の commit message に PLAN を関門にする理由は書かれていない。**理由の記録が引けない** |
| ④ 過去に主体移管の裁定・実測があるか | **有り**。08-17 台帳「PLAN=Qwen」。**ただし逐語で「★消去法」＋「identity が口から引けない」** ＝ 直接の証拠ではない |
| ⑤ False にすると何が失われるか | **`CREATED` で機械が自動的に PLAN を作る**ようになる。失われるのは「設計計画を人が一度見る」機会。**その機会が現在も使われているかは、③が未確定なため判定できない** |

**∴ 「古い制約の可能性が高い」とは言えるが、「不要」とは言えない。**
理由の記録が無く、identity も口から引けないため。**推測で埋めない。**

**PLAN の権限変更は、再武装の二重定義除去とは別の裁定として Taka へ上申する。** 本書では変更しない。

## 6. General Manager 責務表への追加（前提）

**以後、4欄を別々に持つ。1つの「人／機械」判定へ潰さない。**

```
actor_role         _MAP[state][1]            ★名前。主体を決めない
next_operation     _MAP[state][0]            ★NONE/BLOCKED を「機械の番」と混ぜない
machine_supplier   _machine_registry()       ★供給できるか（事実）
authority_barrier  _MAP[state].claude_barrier ★供給させてよいか（政策）
```

**今夜の実証** ―― この4つを1欄で代用した瞬間に HUMAN_BARRIER のラッチが起きた。

## 7. していないこと

`decide_rearm` 未変更 ／ `_MAP` 未変更 ／ 2件の再試行 0 ／ 22・33 へ拡大 0 ／
EVO-0019 の迂回実装 0 ／ 並列実行・負債掃除 0。
