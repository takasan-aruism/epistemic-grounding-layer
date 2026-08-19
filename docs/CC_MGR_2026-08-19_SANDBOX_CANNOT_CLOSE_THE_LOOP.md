# 宛: Taka ―― **★上申: 「sandbox 内で GENERATE/TEST まで閉じる」は ★原理的に 満たせない**

**2026-08-19 ／ ★実装 0 ／ 設計 0 ／ 修正案 0 ／ 実 repo 解禁 0**

---

## 0. 結論（★1行）

```
★★止めている 部品が ★prod repo(`/home/takasan/twoder`)の 中に 在り、
★★sandbox の PLAN は ★そこに 触れない ∴ ★sandbox の 中では ★永久に 閉じない。
```

## 1. ★★決定的な 対照（★今回 初めて 取った）

| task | 経路 | `contract` | **runner は 動いたか** |
|---|---|---|---|
| **`9F26BF5F`** | **★Claude DESIGN の 契約経路** | **有** | **★★動いた** ―― `runner_exit=1` ／ `artifact_sha256='4cca88c8…'`（★成果物 実体あり）／ reason=`RUNNER_FAILED`（★試験が 落ちただけ） |
| `3CF23D43` / `76070397` / `1A9EEBD3` / `02BAA787` | ★goal 経路（Qwen 設計） | 無 | **★一度も 動かない** ―― `runner_exit=null` ／ `artifact_sha256=""` ／ reason=`no provenance supplied` |

```
★★＝ ★いま runner が 実際に 動く 経路は ★★Claude が 骨格と 封印試験を 書いた 契約経路 だけ。
★★＝ ★Claude を 外した 経路は ★実装まで 一度も 到達していない。
```

## 2. ★なぜ そうなるか（★事実・★逐語）

```
`twoder/generate_via_runner.py:282`
    provenance = None   # J1: 実在位置は CREATE payload.knowledge_packet.provenance(★ledger 経路のみ)
    if has_skel and has_tests:      # ★packet 経路（★goal 経路は ここ）→ ★provenance は None の まま
    else:                            # ★ledger 経路（★契約経路は ここ）→ ★ここでだけ 詰めている
```

**★材料は ★最初から 在る（★実測・★4件とも）:**

```
CREATE payload.knowledge_packet.provenance = ★有り（鍵 8〜9個）
   02BAA787 / 3CF23D43 / 76070397 / 1A9EEBD3 ―― ★全件 True
★★＝ ★『存在しない』のでは ない。★『packet 経路が 読んでいない』だけ。
```

## 3. ★2DER は ★また 当てた（★2回目）

**`02BAA787` の PLAN（★2DER が 書いた・逐語）:**

```
requirement 「…provides a function `extract_provenance(context)` … must ★extract the
             `provenance` field from the ★`implementation_packet` within the context …」
steps       「Analyze error logs to confirm provenance is missing in GENERATE/REGENERATE input.」
            「★Inspect PLAN structure to ★locate provenance in ★implementation_packet.」
```

```
★★＝ 直す 場所も 直し方も ★2DER が 自分で 言い当てている（★私は 3回とも 伏せた）。
★★到達している = 停止事実 → 証拠取得 → 原因特定 → 直し方の 提案 → PLAN → 検査。
★★到達していない = ★それを ★どこにも 適用できない。
```

## 4. ★★続行不能の 理由（★1つ・★証拠付き）

```
★① 直す 対象 = `twoder/generate_via_runner.py`（★or `webui.py` の packet 組み立て）
★② `build_planner.PROD_REPO_ROOTS` = (egl, ds, rri, dev-workcell, ★twoder)
★③ `validate_plan` 逐語「target_workspace %r is an ★existing project repo (★forbidden)」
★★∴ ★①を 宛先に した PLAN は ★記録され得ない
★★∴ 2DER が 出せる 最善は ★sandbox の 中の ★おもちゃ（実測: scope 逐語
   「★Sandbox-only investigation and implementation of a provenance restoration module.」）
★★∴ ★おもちゃを 作っても ★本体の GENERATE は 直らない
★★∴ ★そして その おもちゃ 自体も ★同じ 欠陥で GENERATE できない（★3回 再現）
```

**★★＝ ご指示「sandbox 内で GENERATE / TEST まで 閉じたら 停止して 報告」は
★満たせないことが ★証明された。★これが 報告です。**

## 5. ★上申（★これだけ）

```
★★2DER が 自分の 開発ループを 閉じるには ★prod repo(twoder)への 変更が ★1回 要る。
★これは ★安全境界の 変更 ∴ ★Taka の 裁定 事項。★私は 触っていません。

★参考（★私の 決定では ない・★材料のみ）:
  ・変更の 大きさ = ★packet 経路でも ★ledger 経路と 同じ 場所を 読ませる、という 1点
  ・その 場所は ★既に 在る（CREATE payload.knowledge_packet.provenance ／ ★4件とも 有り）
  ・★誰が 書くかは ★別問題（★2DER に 書かせるなら ★prod repo を 宛先に できる 必要が ある）
  ・★SELF_DEV_TOKEN の 予算（初期5）は ★この 解禁に ★そのまま 適用できる 想定
```

## 6. ★MGR が していないこと

```
★実 repo 解禁 0 ／ prod repo への 変更 0 ／ 修正案の 提示 0（★上の「材料」は 事実の 引用のみ）
★設計 0 ／ 契約 0 ／ 骨格 0 ／ 封印試験 0 ／ 実装 0 ／ run_next 0 ／ 手動前進 0 ／ 状態変更 0
★`generate_via_runner.py:282` を 私は 特定済みだったが ★3回とも goal に 書かなかった
   （★2DER が 自力で 到達した ことが ★これで 証明された）
```
