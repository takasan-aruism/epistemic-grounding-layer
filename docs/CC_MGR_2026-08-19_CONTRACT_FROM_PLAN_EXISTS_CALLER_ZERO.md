# 宛: Taka ―― **★変換器は既に在る。★呼び手0。★「欄の名前が違うだけ」**

**2026-08-19 ／ 調査のみ。★実装 0 ／ ★Claude による契約生成 0 ／ ★run_next 0 ／ ★task 前進 0。**

---

## 0. 4点の答え

```
★既存 converter          … ★★在る（`twoder/contract_from_plan.py` ＋ `domain_dw.contract_with_precheck`）
★test_body → immutable_tests … ★★そのまま（★1文字も 変えない＝★名称変換）
★PLAN → skeleton         … ★★決定論で 作れる（★設計判断 ★不要）
★最小不足 1箇所           … ★★`webui.py:542-548`（GENERATE へ 渡す packet を 変換していない）
```

## 1. ★既存 converter（★2DER が書いた・★Claude は1行も書いていない）

```python
twoder/contract_from_plan.py
    contract_from_plan(requirement, target_file, test_plan, test_body)
        → {"skeleton": str|None, "immutable_tests": str|None, "reason": str|None}

twoder/domain_dw.py:101
    contract_with_precheck(plan)      # ★plan 1つを 渡すだけ
        ① precheck_names(plan)  … 判定は 2DER の `name_matches_route`
        ② STOP なら 契約を 作らない（reason="precheck_stop"）
        ③ GO なら contract_from_plan で 組む ＋ 検査の1行を 骨格の説明文へ 機械が 書き写す
```

**★引数が Qwen PLAN の欄と 完全に 一致しています**（`requirement` / `target_file` / `test_plan` / `test_body`）。

## 2. ★★実データで引いた（★純関数・★副作用0・★状態変更0）

`TASK-2DER-7D461717` の **記録済み Qwen PLAN** をそのまま入力:

```
★reason           = ★None（★作れた）
★immutable_tests  = ★1906バイト ／ ★test_body と ★完全一致（★True）
★skeleton         = ★3行が 決定論で 出た:
      def diff_texts(a, b, c):
          """<requirement の 1行>"""
          <<<FILL: ここに実装>>>
```

**＝ 追加判断は 1つも 要りませんでした。**

## 3. ★「名前が違うだけ」と「意味を新しく作る」の切り分け

| 欄 | 種別 | 根拠（逐語） |
|---|---|---|
| `immutable_tests` | **★名前が違うだけ** | 「immutable_tests は test_body を**そのまま**。**1文字も変えない**」 |
| `skeleton` | **★決定論の組み立て**（新しい意味は作らない） | 関数名＝`from impl import <名>` から抽出／引数の数＝呼出の括弧を数える／`a, b, c…` に置換／説明文＝`requirement` の1行／本体＝固定文字列 `<<<FILL: ここに実装>>>` |

```
★★設計判断が 要るもの = ★無い（★実測で reason=None）
★★但し 制約が 1つ 在る = `target_file` が ★"impl.py" 以外だと reason="unexpected_target"
   （★今回の Qwen PLAN は "impl.py" ∴ 通った）
```

## 4. ★RUNNER が要求する schema（正確に）

```
★packet 経路（generate_via_runner.py:279-286）
   packet["skeleton"] と packet["immutable_tests"] が ★両方 not None なら 採用
   ★SHA の 検査は ★無い（★文字列2本だけ）

★ledger 経路（:288-309・★packet に 無い ときの 落ち先）
   CREATE payload["contract"] = {skeleton, immutable_tests,
                                 skeleton_sha256, immutable_tests_sha256, sealed_by}
   ★SHA 一致を 検査（不一致= CONTRACT_SHA_MISMATCH）
```

**★`contract_from_plan` の返り（文字列2本）は ★packet 経路の要求と ★同型です。**

## 5. ★Claude DESIGN 経路では 誰が 2欄を 作っていたか

```
★Claude が 契約文書に <<<2DER:SKELETON>>> / <<<2DER:IMMUTABLE_TESTS>>> を ★書く
 → `contract_seal.extract_contract` が ★決定論で 抽出（逐語「抽出経路は LLM 呼出を一切含まない」）
 → `submit` が 封印し ★CREATE payload["contract"] へ
★★＝ 機械は 抽出と封印だけ。★2欄の 著者は ★Claude だった。
★★＝ `contract_from_plan` は ★その著者の位置に ★2DER を 置く 部品。
```

## 6. ★★最小不足 ―― 1箇所

**`twoder/webui.py:542-548`（GENERATE の actor `cw`）**

```python
542  ip = plan["payload"].get("implementation_packet") if plan else create["payload"].get("knowledge_packet")
...
548  gr = generate_via_runner.generate({**(ip or {}), "task_id": tid}, attempt)
```

```
★`ip` = Qwen の implementation_packet（★skeleton / immutable_tests を 持たない）
★∴ generate():283 が False → ledger 経路 → CREATE に contract 無し → ★SPEC_INCOMPLETE_NO_CONTRACT
★★ここで `contract_with_precheck(ip)` を 通していない。
```

**★呼び手の実測:**

```
`contract_with_precheck` を 呼ぶ 場所 = ★domain_dw(定義) と manager_v0(素通しの 別名) ★のみ
★それ以外からの 呼び出し = ★★0件
＝★★置いてあるが 繋がっていない（★今夜 何度も 出た 型）
```

## 7. ★確かめていないこと（★隠さない）

```
★`precheck_names` / `name_matches_route` が この plan で GO か STOP かは ★引いていない
   （★`_use` が 記録を 書く ∴ 観測だけの 今回は 呼ばなかった）
   ＝★`contract_with_precheck` の ★②の 分岐は ★未検証。★通ったのは 内側の `contract_from_plan`。
★`target_file` が "impl.py" 以外の PLAN で どうなるかは ★測っていない
★配線した場合に GENERATE の 先（runner 実行・test の 合否）が どうなるかは ★未知
```

## 8. していないこと

```
★実装 0 ／ 契約 0 ／ skeleton 0 ／ immutable_tests 0 ／ test 0
★run_next 0 ／ task 前進 0 ／ 状態変更 0 ／ 待ち行列 変更 0
★Claude DESIGN 版 11件は ★触っていない（★block_task も 実行していない）
```
