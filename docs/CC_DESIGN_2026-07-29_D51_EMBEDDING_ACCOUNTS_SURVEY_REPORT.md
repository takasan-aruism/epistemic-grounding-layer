# Embedding 勘定科目システム 現況報告（D-51）

- `BUILD_ROLE: 参照`（**調査のみ。★Python を1行も変えていない・仕様変更なし・新規設計なし・配線変更なし・投入なし・台帳直読なし**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-29 / TYPE=FINDING
- **運用方針 確認済（版: `v2.8`）** / **典拠**: Taka「Embedding勘定科目システム 現況調査（実装変更禁止）」逐語

---

## 0. ★一枚の答え
| | **設計** | **実装** | **配線** | **実運用** |
|---|---|---|---|---|
| **Embedding（ベクトル埋め込み）** | **あり** | **あり**（研究スクリプト1本） | **★なし** | **★なし** |
| **勘定科目（account）** | **あり** | **あり**（RRI に強制つき） | **★なし** | **★なし** |
| **Embedding → 勘定科目の決定** | **あり**（研究として） | **★研究出力まで** | **★なし** | **★なし** |

> **★最も端的な証拠1つ**: **勘定科目表そのもの（`rri/rri/rthread_chart.json`）が★存在せず、★どのコードもそれを作らない。**
> **∴ 勘定科目を使う関数を呼べば、必ず `RThreadChartUnavailable` で止まる**（fail-closed）。**∴ 実運用は「なし」で確定する。**

---

## 1. 初期設計の所在
**証拠（走査・`head` 不使用）**
```
egl/docs の md: embed を含む 36本 / 勘定科目・account を含む 101本 / ★両方を含む 22本
（総件数 22 / 確認 22 / 打ち切り無し）
```
**主要文書（両方を含む22本のうち、勘定科目軸そのものを扱うもの）**
| 文書 | 位置づけ | 現在も有効か |
|---|---|---|
| `CC_DESIGN_2026-07-25_RTHREAD_STAGE2b_REDESIGN_PLAN.md` | **設計の本体。** 「勘定科目＝ベクトルから自然抽出され Frozenset として凍結される離散な軸」 | **★有効**（失効の記載を見つけていない） |
| `SPEC_EMBED_AXES_v0.1.md` | 埋め込み軸の仕様 | ★有効 |
| `CC_DESIGN_2026-07-25_ACCOUNT_AXIS_NAMING_JUDGMENT_ADJREQ.md` / `..._ADJRESULT.md` | 軸命名の裁定要求と結果 | ★有効 |
| `CC_DESIGN_2026-07-25_RTHREAD_2b-r2_AXIS_FREEZE_HANDOFF.md` / `2b-r3_REFREEZE_...` | 軸の凍結・再凍結 | ★有効 |
| `CC_IMPL_2026-07-25_EMBED_AXES_BUILT.md` | 実装報告 | ★有効 |

| 判定 | |
|---|---|
| **設計** | **★あり。** 前提も明記されている——**「決定論素性マイニングは NO_STABLE(DE-0521)」「前回の『場(field)化+mass保存』案は Taka 否定」** |
| **失効か** | **★失効の記載を見つけていない。** **ただし `egl/docs` の md を全数読んでいない**（§7-1） |

---

## 2. 実装状況
**証拠（走査・`head` 不使用）**
```
全 repo で "embed" を含む .py: ★8本（総8 / 確認8 / 打ち切り無し）
  egl/structure/s_account_axes.py / s_account_axis_names.py / s_embed_axes.py
  egl/structure/s_record_tags.py  / s_rthread_2br3.py
  twoder/live_worker_scaffold.py  / twoder/tools/codegen_run_fn.py
  twoder/regression/test_dedicated_issue_fetch.py
```
### 2-1. ★本番コードの2本は「埋め込み」ではない（実読）
```
twoder/live_worker_scaffold.py:53  "… embedded commands must never be adopted …"   ← 英単語
twoder/tools/codegen_run_fn.py:129 "… now embedded in the harness."                ← 英単語
```
> **∴ 本番コードにベクトル埋め込みを使う箇所は★0件である。**

### 2-2. ★実装は在る（研究スクリプト1本）
```
egl/structure/s_embed_axes.py:28  MODEL = "intfloat/multilingual-e5-small"
                          :61-66  import torch / from transformers import AutoModel, AutoTokenizer
                                  AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
自称: 「CPU 意味埋め込みで内容テキストをベクトル化し、安定軸が実在するかを負の制御付きで測る」
      「measure-first: 出なければ NO_STABLE_AXES(正当な結果)」「LLM 不使用」
```
| 判定 | |
|---|---|
| **実装** | **★あり**（実モデルを CPU で使う。revision pin つき） |
| **性格** | **★経験的テスト**（「安定軸が実在するかを測る」）。**製品機能ではない** |

### 2-3. ★誰から呼ばれるか
```
外部参照（自ファイルを除く・打ち切り無し）:
  s_embed_axes 7行 / s_account_axes 2行 / s_rthread_2br3 1行 / 他2本 0行
実体: egl/structure/s_account_axis_names.py:24 と s_record_tags.py:100 の★2箇所のみ
```
> **∴ 参照はすべて `egl/structure/` の内側である。** **★本番コードからの参照は0件。**
> **∴ 未使用・廃止ではなく★「研究として生きているが、本番から呼ばれていない」。**

---

## 3. Ledger との接続
| 判定 | |
|---|---|
| **設計** | **あり**（勘定科目を問いに付与する＝`I2` 科目次元の保存則） |
| **実装** | **★あり**（`rri/rri/request_thread.py`。`raise_question(…, account_id=UNCLASSIFIED)` / off-chart は `ValueError`） |
| **配線** | **★なし** |
| **実運用** | **★なし** |

**★どこで止まっているか（証拠）**
```
再現: ls rri/rri/rthread_chart.json          → ★存在しない
再現: grep -rn "rthread_chart" --include=*.py 全5repo（打ち切り無し）
      → ★1行のみ。request_thread.py:19 の既定パス定義そのもの。★作る側が居ない

request_thread.py:117  _, _accounts = _load_chart()      ← ★引数検査より前に必ず呼ばれる
             :93-102   不在/破損は RThreadChartUnavailable(fail-closed)
```
> **∴ `raise_question` は★`account_id=UNCLASSIFIED` でも必ず例外になる**（chart 読み込みが引数検査より前）。
> **∴ 「Ledger 登録時に勘定科目を Embedding から決定する経路」は★存在しない。**
> **★止まっている場所は2つ**: **(a) `request_thread` に本番の呼び手が0**（`G-45`）／**(b) 勘定科目表が存在しない**。

---

## 4. EGL との接続
| 判定 | |
|---|---|
| **設計** | **★見つけていない**（探索範囲: §7-2） |
| **実装** | **★なし** |
| **配線** | **★なし** |
| **実運用** | **★なし** |

**★証拠（利用していない理由）**
```
再現: EGL 本体(egl/egl)の書き込みは3箇所のみ（本日 D-44 で実測・打ち切り無し）
      core.py:44(ロック) / core.py:119(events.jsonl) / de_admission.py:167(DE 台帳)
再現: grep -rli "embed" --include=*.py egl/egl → ★0本
```
> **∴ EGL 本体に埋め込みを使うコードは★1本も無い。**
> **∴ EGL 登録時に Embedding 勘定科目を利用していない。** **理由は「実装が EGL 側に存在しないから」である。**

---

## 5. RRI との接続
| 判定 | |
|---|---|
| **設計** | **★あり**（`RTHREAD` 段2a=「accounts 機械核（chart 検証／suspense 決着／account 保存 load-bearing）」） |
| **実装** | **★あり**（`request_thread.py` に 36行。`UNCLASSIFIED` の特殊値・`UNCLASSIFIED_FORBIDDEN_DISPOSAL`・`check_account_conservation`） |
| **配線** | **★なし**（`request_thread` の本番呼び手は0＝`G-45`・本日実測） |
| **実運用** | **★なし** |

**★実装の中身（実読・強制されている規則）**
```
UNCLASSIFIED_FORBIDDEN_DISPOSAL = ("RESOLVED",)
  → 分類保留(UNCLASSIFIED)の問いを「解決」で閉じることを★禁止（会計の suspense と同じ扱い）
raise_question: off-chart account_id は ValueError（D2）
check_account_conservation: 科目次元の保存則（I2）
```
> **★設計は「宣言」ではなく「例外で強制」の形で実装されている。** **★ただし呼ばれない。**

### 5-1. ★MGR が渡した材料の検証（「合わせるな」の指示に従い確かめた）
| MGR の材料 | 私の検証 |
|---|---|
| 段2a は「accounts 機械核」と自称している | **★正しい**（git commit 題名を実読） |
| `egl/structure` の account/embed 系は研究スクリプトで本番参照0件 | **★正しい**（§2-3 で実測） |
| 段2b の作り直しは「勘定科目の軸」が対象で「account 次元は soft」 | **★正しい**（`STAGE2b PLAN §0` を実読） |
> **★3件とも誤っていなかった。** **ただし私は原典を実読して確かめた。** **合わせていない。**

---

## 6. Execution Architecture 上の位置づけ
| 判定 | |
|---|---|
| **Capability / Edge / Cycle として定義されているか** | **★されていない** |

**★証拠**
```
再現: 2DER_EXECUTION_ARCHITECTURE.json の components(23) / edges(11) / entrypoints(8) を全数確認
  → embed / account を扱う component・edge は★0件
再現: 同 md で「勘定科目」への言及は Gap 側にのみ在る
  G-02「勘定科目が EGL 登録経路に繋がっていない」（未着手）
```
> **∴ 資料上、この機能は★「機構」としてではなく★「欠落（`G-02`）」としてのみ登記されている。**
> **★これは資料の誤りではない。** **配線が無い以上、component として書けば実態と食い違う。**

---

## 7. ★未確認（推測で補完しない）
| # | 未確認 | 誰が・いつ |
|---|---|---|
| **1** | **`egl/docs` の md を全数読んでいない**（両方を含む22本を一覧し、うち実読は6本）。**∴「失効の記載は無い」ではなく「見つけていない」** | CC-α / 要請時 |
| **2** | **EGL 側の設計文書を個別に探していない**（`egl/egl` のコード走査で0だったため）。**∴「設計は無い」ではなく「見つけていない」** | CC-α / 要請時 |
| **3** | **`s_embed_axes.py` を実行していない。** **★出力（安定軸が出たのか NO_STABLE_AXES だったのか）を確かめていない** | **★これは「実装変更禁止」の範囲外だが、実行は副作用を持つため行っていない。MGR の判断を仰ぐ** |
| **4** | **`rthread_chart.json` が過去に存在した可能性を確かめていない**（git 履歴を見ていない） | CC-α / 要請時 |

## 8. ★禁止事項の遵守
- **Python を1行も変えていない。** **仕様変更・新規設計・配線変更をしていない。**
- **推測で補完していない。** **「たぶん」「あるはず」を使っていない。**
- **調査中に修正していない。** **★配線したくなる場面が2つ在ったが**（`rthread_chart.json` を作る／`request_thread` を呼ぶ）**両方とも止めた。**
- **走査に `head`/`tail`/`-m`/`limit` を1つも使っていない。** **各走査に総件数・確認件数・打ち切り有無を書いた。**
- **台帳を直読していない。**

---
*CC-α「Embedding 勘定科目システム 現況報告」（D-51・調査のみ）。★一枚の答え=**Embedding は設計あり・実装あり（研究スクリプト1本）・配線なし・実運用なし／勘定科目は設計あり・実装あり（RRI に例外で強制）・配線なし・実運用なし／Embedding→勘定科目の決定は研究出力まで**。最も端的な証拠は**勘定科目表 `rri/rri/rthread_chart.json` が存在せず、どのコードもそれを作らない**こと ∴ 勘定科目を使う関数を呼べば必ず `RThreadChartUnavailable` で止まる（fail-closed）∴ 実運用は「なし」で確定する。★①初期設計=`egl/docs` の md で embed 36本／account 101本／**両方 22本**、本体は `RTHREAD_STAGE2b_REDESIGN_PLAN`（「勘定科目＝ベクトルから自然抽出され Frozenset として凍結される離散な軸」）＋`SPEC_EMBED_AXES_v0.1` ほか。**失効の記載は見つけていない**（全数読んでいないので「無い」とは書かない）。★②実装=`embed` を含む .py は8本だが、**本番2本は英単語「embedded」のコメントで埋め込みではない** ∴ 本番にベクトル埋め込みは**0件**。実装は `egl/structure/s_embed_axes.py` 1本で、`intfloat/multilingual-e5-small` を revision pin つきで CPU 実行する**経験的テスト**（「安定軸が実在するかを測る」「出なければ NO_STABLE_AXES が正当な結果」）。外部参照はすべて `egl/structure` 内側の2箇所のみで**本番からの参照は0** ∴ 未使用・廃止ではなく「研究として生きているが本番から呼ばれていない」。★③Ledger=設計あり・実装あり（`raise_question` の `account_id`・off-chart は `ValueError`）だが**配線なし・実運用なし**。止まっている場所は2つ=**(a) `request_thread` の本番呼び手が0**（`G-45`）**(b) 勘定科目表が存在せず作る側も居ない**（`grep` で1行＝定義のみ）。しかも `_load_chart()` は引数検査より前に呼ばれるので**`UNCLASSIFIED` でも必ず例外**になる。★④EGL=**設計は見つけていない／実装・配線・実運用なし**。EGL 本体の書き込みは3箇所のみで `egl/egl` に `embed` を含む .py は0本 ∴ 利用していない理由は「実装が EGL 側に存在しないから」。★⑤RRI=設計あり（段2a「accounts 機械核」）・実装あり（36行。`UNCLASSIFIED_FORBIDDEN_DISPOSAL` で分類保留の問いを「解決」で閉じることを禁止＝会計の suspense と同じ扱い、`check_account_conservation` で科目次元の保存則）だが**配線なし・実運用なし**——**設計は宣言ではなく例外で強制の形で実装されているが呼ばれない**。MGR が渡した材料3件は**すべて正しかったが、原典を実読して確かめており合わせていない**。★⑥Execution Architecture=components 23／edges 11／entrypoints 8 を全数確認し **embed/account を扱うものは0件**で、資料上は**機構ではなく欠落（`G-02`）としてのみ登記**されている——配線が無い以上 component として書けば実態と食い違うので資料の誤りではない。★未確認4件（`egl/docs` の md を全数読んでいない＝「失効の記載は無い」ではなく「見つけていない」／EGL 側の設計文書を個別に探していない／**`s_embed_axes.py` を実行しておらず出力が安定軸だったのか `NO_STABLE_AXES` だったのか確かめていない**——実行は副作用を持つため行っておらず MGR の判断を仰ぐ／`rthread_chart.json` が過去に存在した可能性を git 履歴で確かめていない）。★禁止事項の遵守=Python を1行も変えず・推測で補完せず・調査中に修正せず、**配線したくなる場面が2つ在ったが（`rthread_chart.json` を作る／`request_thread` を呼ぶ）両方とも止めた**。走査に `head` 等を1つも使わず各走査に総件数・確認件数・打ち切り有無を記載し、台帳を直読していない。*
