# 宛: Taka ―― **Qwen の test_body が「対象を検証している」ことを、いま誰が保証しているか**

**2026-08-19 ／ 調査のみ。★実装 0 ／ test 0 ／ PLAN 0 ／ 契約 0 ／ run_next 0 ／ 状態変更 0。**

---

## 【1】★既存 guard ―― **PLAN 時点には 無い。★下流に 2つ 在り、★今夜 実際に 効いた**

```
★① validate_plan（PLAN を 記録する 直前）… ★★見ていない
      `tests_ok = bool(test_plan) and bool(test_body.strip()) and bool(test_file.strip())`
      ＝★★3つの 欄が ★空でない ことだけ。★中身は 1文字も 見ない。

★② precheck_names → name_matches_route（★契約変換の 直前）… ★★効く（★決定論）
      EAACCE21 実測 = {"verdict":"STOP","line":"★実装する 名前が 読めない(★from impl import が 無い)"}
      ★2回引いて 同じ。

★③ contract_from_plan（★②を 通った 後）… ★★効く（★決定論）
      「from impl import」の 行が 無ければ reason="no_function_name" で 何も 作らない。

★④ AUDIT の 語彙に `test_not_load_bearing` が ★在る（workcell.py:35 / adapters.py:74）
      ★但し ★決定論の 検知器では ない ―― ★LLM auditor へ 渡す 分類名の 一覧の 1語。
      ★かつ 見る 対象は ★出来上がった コード（★PLAN 時点では 効かない）。
```

**★規則そのものは 既に 明文で 在ります（`build_planner.py:162` の プロンプト・逐語）:**

> 「Import the code under test with **"from impl import \<name\>"** — the module is always impl.」

```
★★＝ ★指示は 在る。★検査が 無い（★出力を 突き合わせていない）。
```

## 【2】★`validate_plan` が見落としている **最小条件（1つ）**

```
★★「test_body が target_file のモジュールを import していること」
   ＝ 現在の `tests_ok` は ★存在の 3点だけ。★参照関係を 1つも 見ない。
★これが 無いため ★★対象を 差していない 試験でも ★PLAN が 記録される。
   （★記録された 後で ②③ が 落とす ∴ ★手戻りが 発生する）
```

**★手戻りの実測（`TASK-2DER-EAACCE21` 1件で発生した空回り）:**

```
GENERATE 1 ／ REGENERATE 1 ／ AUDIT 2 ／ DISPOSE 2 ／ UPPER_REVIEW 1
★すべて reason=SPEC_INCOMPLETE_NO_CONTRACT ／ runner_exit=null ／ diff=0B
★＝ ★runner は 一度も 動いていない のに ★7工程が 回った。
```

## 【3】★既存部品で塞げるか ―― **★塞げている。★但し 位置が 遅い**

```
★判定能力 = ★★既に 在る（②③ ＝ 決定論・LLM 0回・2回引いて同じ）
★足りないのは ★★位置だけ ―― ★同じ判定を ★`validate_plan` の 時点で 引けば
   ★PLAN が 記録される 前に 落ちる（★`build_planner` は 無効なら 何も 記録しない）。
★★新しい 語も 新しい 台帳も 新しい 口も ★要らない 見込み。
```

## 【4】★新しい判断能力が必要か ―― **★「今の変換器の水準を保つ」なら 不要。★広げるなら 必要**

**★過去の Qwen PLAN 358件を 数えました（★`identity=2der-qwen-build-planner`）:**

| 母数 | 件数 |
|---|---|
| Qwen PLAN 総数 | **358** |
| うち `target_file == "impl.py"`（★変換器に届き得る母数） | **171** |

**★その 171件の 内訳（★test_body の 参照の 形）:**

| 形 | 件数 | 変換器を 通るか |
|---|---|---|
| **A `from impl import …`** | **68（40%）** | **★通る** |
| **B `import impl`** | **87（51%）** | **★通らない**（★`from impl import` を 探すため） |
| **C 対象を import しない**（自己定義 / mock を含む） | **16（9%）** | **★通らない** |

```
★試験の中の 「非 test の def」の 数 = {0: 101件, 1: 51件, 2: 14件, 3: 5件}
   ＝★★70件（41%）が ★試験の中で 何かを 自分で 定義している。
```

```
★★∴ 新しい 判断が 要るのは ★★B（51%）を 通したい 場合だけ
   （★`import impl` + `impl.<名>` の 形から 名前を 取る ＝ ★★意味を 新しく 作る 話では ない）。
★★A の 水準の まま で よいなら ★新しい 判断能力は ★不要（★位置を 前へ 出すだけ）。
```

## 【★参考】④ 2件の構造差（★判断ではなく 構造項目）

| 項目 | `7D461717`（GO） | `EAACCE21`（STOP） |
|---|---|---|
| PLAN identity | `2der-qwen-build-planner` | 同じ |
| `validate_plan` | 通過 | **通過**（★両方通る） |
| `target_file` / `test_file` | `impl.py` / `test_impl.py` | **同じ** |
| `test_body` の大きさ | 1906B | 1745B |
| **`from impl import`** | **★有り** | **★★無し** |
| **試験内の 非 test の def** | **★0個** | **★★1個**（`def create_unified_diff(...)` ＝ 逐語 `# Mock the function to be tested` / `# Placeholder implementation`） |
| `def test_` の数 | 8 | 9 |

```
★★差は ★2項目だけ（import の 有無 ／ 非test def の 有無）。★他は 揃っている。
★★同じ Qwen が ★同じ種類の 依頼で ★2回 違う 形を 出した ＝ ★揺れている。
```

## していないこと

```
★実装 0 ／ test 0 ／ test_body 0 ／ PLAN 0 ／ 契約 0 ／ skeleton 0
★run_next 0 ／ task 手動前進 0 ／ 状態変更 0
★`7D461717` は 触っていない ／ Claude DESIGN 版 11件も 触っていない
★`validate_plan` / `contract_from_plan` / `build_planner` の プロンプトを ★1文字も 変えていない
```
