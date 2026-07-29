# 設計/監査 → MGR（写: Taka / IMPL）: **D-52 — ★Taka の指摘が原典で裏づけられた。`rthread_chart.json` は「人が書く表」ではなく「MINING が生成する派生物」である**

- `BUILD_ROLE: 参照`（**調査のみ。★科目表を作っていない・コードを変えていない・配線していない・投入なし・台帳を直読していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-29 / TYPE=FINDING
- **運用方針 確認済（版: `v2.8`）** / **典拠**: Taka（2026-07-29 逐語・5項目）

## 0. ★結論
> **Taka の指摘は★正しい。** **原典が明示的に「人が定義する固定表ではない」と書いている。**
> **∴ 「表が無いから止まる」は★現象としては正しいが、★枠組みとしては逆だった。**
> **表は★入力ではなく出力である。** **無いのは「書き忘れ」ではなく「生成する段に到達していない」。**

---

## 1. 問1 — `rthread_chart.json` は何を想定したものか
### **★答え: (2) Embedding／MINING 結果から自動生成される派生物**
**逐語（`SPEC_RTHREAD_STAGE2a_v0.1.md`・実読）**
```
:4  > imagined な production account 名を一切導入しない(★実 chart は stage 2b の MINING で生成)。
:5  > 2a は UNCLASSIFIED + ★純テスト fixture chart(ACCT_TEST_A/B)だけで機構を検証。
:22 # 有効 account を定める versioned chart。★DERIVED/versioned(never SoR, G-5)。
:23 # 実体はテスト fixture(RTHREAD_CHART env)/ ★本番は stage2b の MINING 生成物。fail-closed。
```
| | |
|---|---|
| **(1) 人間が手動定義する固定科目表** | **★違う。** 「imagined な production account 名を一切導入しない」と明示 |
| **(2) 自動生成される派生物** | **★これである。** 「DERIVED/versioned(never SoR)」「本番は stage2b の MINING 生成物」 |
| **(3) 一時的な仮実装** | **★一部そう。** `ACCT_TEST_A/B` は**テスト fixture として意図的に置かれた仮**である |

> **∴ `rthread_chart.json` が無いのは★設計どおりの状態である。** **stage2b の MINING が本番 chart を生成する段に、まだ到達していないだけである。**
> **★`RTHREAD_CHART` 環境変数が在るのは、fixture を差し込むためである。** **人が本番表を書く想定ではない。**

## 2. 問2 — Embedding から科目が形成される手順はどこまで定義されているか
**逐語（`RTHREAD_STAGE2b_REDESIGN_PLAN` §2・実読）**
```
2b-r1: ベクトル化→★安定な密方向(軸候補)が在るかを決定論抽出で測る。
       出口 (i) K 個の安定軸が出る→Frozenset 候補として凍結へ
            (ii) 拡散・軸ほぼ無し→★その他優勢=正当な初期状態
2b-r2(軸が出た時のみ): 抽出軸を versioned Frozenset ★ACCOUNT_AXES に凍結。
       各問いに軸ごとの密度(多重所属可)+ 全軸で閾値未満なら★その他。
2b-r3: 再凍結規律。その他が育って濃い方向を持ったら稀に・意図的に・versioned で新軸を追加凍結。
```
| どこまで定義されているか | |
|---|---|
| **定義されている** | **測る→凍結→多重所属→濃淡→再凍結** の5段すべて |
| **★定義が切れている箇所（名指し）** | **★凍結した `ACCOUNT_AXES` を、`_load_chart()` が読む `rthread_chart.json` にする手順が★1行も無い。** |
| **証拠** | **`STAGE2b_REDESIGN_PLAN` の `chart` 言及は★0行**（`SPEC_RTHREAD_STAGE2a` は41行）。**名前も違う**（`ACCOUNT_AXES` ⇄ `rthread_chart.json`） |

> **∴ 「科目を作る側」と「科目を使う側」が、★別の名前で設計されており、繋ぐ手順が書かれていない。**

## 3. 問3 — 出力を chart / `request_thread` へ渡す設計・コード・未実装箇所
**★MINING の本体は実在する（実読）**
```
egl/structure/s_mine_accounts.py
  "chart of accounts の決定論マイニング(RTHREAD stage 2b-1 / MINING_SPEC v0.1)"
  "「account を発明しない」の本体。DE ledger + rri_records を決定論クラスタリングし、
   ★安定 chart が在るかを測定する(第一目的は chart 生成でなく安定性測定)"
  出口: 負の制御を上回らなければ chart_status=NO_STABLE_STRUCTURE を記録し ★chart を捏造しない
  出力: ACCOUNT_CHART_CANDIDATE.jsonl / ACCOUNT_CHART_STABILITY.json
```
**★出力物は実在する（存在確認のみ。★内容は読んでいない）**
```
ACCOUNT_CHART_CANDIDATE.jsonl      存在する
ACCOUNT_CHART_STABILITY.json       存在する
ACCOUNT_AXES_FREEZE_CANDIDATE.jsonl 存在する
ACCOUNT_AXIS_NAMES.jsonl           存在する
```
**★渡す経路（走査・打ち切り無し・cwd を明示して再実行した）**
```
再現: grep -rn "rthread_chart" --include=*.py 全5repo → ★1行のみ
      = request_thread.py:19 の既定パス定義そのもの。★候補を chart にする側が居ない
```
| 判定 | |
|---|---|
| **設計** | **★無い**（`STAGE2b PLAN` に chart への言及が0行） |
| **コード** | **★無い**（`ACCOUNT_CHART_CANDIDATE` → `rthread_chart.json` の変換が1行も無い） |
| **★未実装箇所（名指し）** | **`ACCOUNT_CHART_CANDIDATE.jsonl`（生成済）→ `rthread_chart.json`（`_load_chart` が読む）の1段** |

## 4. 問4 — 「表にない科目は例外」の位置づけ
**逐語（`SPEC_RTHREAD_STAGE2a_v0.1.md:9`）**
```
設計判断(プロトタイプで実証済み・ADJUDICATION_SENSITIVE):
  D1 suspense 再定義 / ★D2 chart検証=machine / D3 account保存 load-bearing
```
| 3択 | 判定 |
|---|---|
| **(1) 恒久仕様** | **★そう読める。** `D2` は `ADJUDICATION_SENSITIVE` な設計判断として明記され、**★撤回の記載を見つけていない** |
| (2) 初期化後の安定運用だけを想定 | **★根拠を見つけていない** |
| (3) 仮勘定実装の残骸 | **★違う。** `UNCLASSIFIED`（仮勘定）は**残骸ではなく `D1` として設計されたもの** |

> **★ただし1つ、確実に取り下げられたものが在る**（逐語・`STAGE2b PLAN §0`）:
```
「hard 不変量は問い台帳(stage1 I1)のみ。★account 次元は soft。
  前回私が account に mass 保存を課したのは誤り→★取り下げ済み。」
```
> **∴ 取り下げられたのは `D3`（account保存 load-bearing）であって、`D2`（chart 検証）ではない。**
> **★そして `D3` はコードに★残っている**: `request_thread.py:281 def check_account_conservation(...)`。
> **∴ ★「取り下げ済み」と書かれた制約が、コードには残っている。** **これは新しい発見である**（`G-62` として登記）。

## 5. 問5 — 固定科目表方式へ変更した裁定・DE・仕様変更は存在するか
> **★存在しない。**
```
探索範囲: egl/docs の md で embed と account の両方を含む★22本を一覧し、
          うち chart の定義・変更に関わりうる4本を実読
          (SPEC_RTHREAD_STAGE2a_v0.1 / STAGE2b_REDESIGN_PLAN / SPEC_EMBED_AXES_v0.1 / SPEC_RTHREAD_STAGE1_v0.2)
結果    : ★「chart を人が定義する」に変更した裁定・DE・仕様変更を1件も見つけていない。
          逆に STAGE2a が「実 chart は stage2b の MINING で生成」と明記している。
```
> **∴ Taka の指示どおり報告する: ★これは「設計の変質」ではなく★「未完」である。**
> **★構想は変わっていない。** **生成側（MINING）は在り、使う側（chart 検証）も在り、★繋ぐ1段が未実装である。**

---

## 6. ★私の落ち度（本日4回目の false negative・自己申告）
```
私が打った: cd /home/takasan/egl/docs の状態で
            grep -rl "ACCOUNT_AXES" --include=*.py ds rri egl dev-workcell twoder → ★0
★誤りの機構: cwd が egl/docs のため、パス ds/rri/egl/… が存在しなかった。
正しい結果: cd /home/takasan で再実行 → ★17行。ACCOUNT_CHART_CANDIDATE も出た。
```
> **★これは本日4回目の false negative である**（`head -8` ／ 存在しないパス ／ `git diff HEAD~1` ／ 本件）。
> **★しかも「作業ディレクトリに依存するコマンドは絶対パスか明示 cd で始める」は、★本日 v2.5 §4-17 として作られた規律である。**
> **★私はその規律に、本日3度違反している。**
> **★4回とも「0 を疑う」で自分で止めた。** **★だが止めているだけで、0 が出ない打ち方に変えていない。**
> **★もし今回止めていなければ、「MINING は存在しない」と Taka に報告していた。** **★事実と正反対である。**

## 7. ★未確認（推測で補完しない）
| # | 未確認 | 誰が・いつ |
|---|---|---|
| 1 | **`ACCOUNT_CHART_CANDIDATE.jsonl` の中身を読んでいない**（台帳直読の禁止）。**∴ `chart_status` が `NO_STABLE_STRUCTURE` なのか、安定 chart が出ているのか★分からない** | **★これが次に最も効く1点である。** MGR の判断を仰ぐ |
| 2 | **`s_mine_accounts.py` / `s_embed_axes.py` を実行していない**（副作用があるため） | MGR の判断待ち |
| 3 | **22本のうち実読は4本**（`chart` 言及の件数で絞った）。**∴「変更裁定は無い」ではなく「見つけていない」** | CC-α / 要請時 |
| 4 | `rthread_chart.json` が過去に存在したかを git で確かめていない | CC-α / 要請時 |

## 8. ★禁止事項の遵守
- **科目表を作っていない。** **コードを変えていない。** **配線していない。**
- **3択を「たぶん」で埋めていない**（根拠が無い項目は「見つけていない」と書いた）。
- **`head`/`tail`/`-m` を使っていない。** 各走査に件数を書いた。
- **MGR の枠組み（「表が無いから止まる」）に合わせていない。** **★逆であると書いた。**
- **台帳を直読していない**（存在確認のみ・内容は読んでいない）。

---
*CC-α D-52（調査のみ）。★結論=**Taka の指摘は正しく、原典が明示的に「人が定義する固定表ではない」と書いている** ∴「表が無いから止まる」は現象としては正しいが枠組みとしては逆で、**表は入力ではなく出力**であり、無いのは「書き忘れ」ではなく「生成する段に到達していない」。★問1=**(2) 自動生成される派生物**（`SPEC_RTHREAD_STAGE2a_v0.1` 逐語「imagined な production account 名を一切導入しない(**実 chart は stage 2b の MINING で生成**)」「2a は UNCLASSIFIED + **純テスト fixture chart(ACCT_TEST_A/B)** だけで機構を検証」「**DERIVED/versioned(never SoR, G-5)**」「本番は stage2b の MINING 生成物」）∴ chart が無いのは**設計どおりの状態**で、`RTHREAD_CHART` env は fixture 差し込み用であり人が本番表を書く想定ではない。★問2=`STAGE2b PLAN §2` は測る→凍結→多重所属→濃淡→再凍結の5段すべてを定義しているが、**凍結した `ACCOUNT_AXES` を `_load_chart()` が読む `rthread_chart.json` にする手順が1行も無い**（同 PLAN の `chart` 言及は**0行**、`SPEC_RTHREAD_STAGE2a` は41行。名前も `ACCOUNT_AXES` ⇄ `rthread_chart.json` で違う）∴ **作る側と使う側が別の名前で設計され繋ぐ手順が書かれていない**。★問3=MINING の本体 `egl/structure/s_mine_accounts.py` は実在し（「account を発明しない」の本体・決定論クラスタリング・**負の制御を上回らなければ `chart_status=NO_STABLE_STRUCTURE` を記録し chart を捏造しない**）、出力4ファイルも実在する（**存在確認のみ・内容は読んでいない**）が、**`rthread_chart` への言及は全5repo で1行（定義そのもの）のみ** ∴ 設計もコードも無く、**未実装箇所は「`ACCOUNT_CHART_CANDIDATE.jsonl`（生成済）→ `rthread_chart.json`」の1段**。★問4=`D2 chart検証=machine` は `ADJUDICATION_SENSITIVE` な設計判断として明記され撤回の記載を見つけていないので**(1) 恒久仕様と読める**（(3) 残骸は違う——`UNCLASSIFIED` は `D1` として設計されたもの）。**ただし確実に取り下げられたものが在り**、`STAGE2b PLAN §0` 逐語「account 次元は soft。前回私が account に mass 保存を課したのは誤り→**取り下げ済み**」＝取り下げは `D3`（account保存）であって `D2` ではない。**そして `D3` はコードに残っている**（`request_thread.py:281 check_account_conservation`）∴ **「取り下げ済み」と書かれた制約がコードに残っている**——新しい発見として `G-62` に登記。★問5=**固定科目表方式へ変更した裁定・DE・仕様変更は存在しない**（両方を含む22本を一覧し chart の定義・変更に関わる4本を実読。逆に STAGE2a が「実 chart は stage2b の MINING で生成」と明記）∴ Taka の指示どおり**「設計の変質」ではなく「未完」**——構想は変わっておらず、生成側も使う側も在り、繋ぐ1段が未実装である。★私の落ち度（本日4回目の false negative）=`cd egl/docs` の状態で `grep … ds rri egl dev-workcell twoder` を打ち **0** を得たが、cwd のためパスが存在しなかっただけで、`cd /home/takasan` で再実行すると **17行**あり `ACCOUNT_CHART_CANDIDATE` も出た。**「作業ディレクトリに依存するコマンドは絶対パスか明示 cd で始める」は本日 v2.5 §4-17 として作られた規律であり、私はそれに本日3度違反している。4回とも「0 を疑う」で自分で止めたが、止めているだけで 0 が出ない打ち方に変えていない。★もし今回止めていなければ「MINING は存在しない」と Taka に報告していた——事実と正反対である**。★未確認=**`ACCOUNT_CHART_CANDIDATE.jsonl` の中身を読んでいない（台帳直読の禁止）∴ `chart_status` が `NO_STABLE_STRUCTURE` なのか安定 chart が出ているのか分からない——これが次に最も効く1点**／`s_mine_accounts.py`・`s_embed_axes.py` を実行していない（副作用があるため）／22本のうち実読は4本（∴「変更裁定は無い」ではなく「見つけていない」）／`rthread_chart.json` が過去に存在したかを git で確かめていない。*
