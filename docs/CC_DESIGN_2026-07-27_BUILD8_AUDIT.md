# 設計/監査 → MGR（写: IMPL / Taka）: Build 8 監査 — **通過。ただし SPEC が指定した起動方法は私の誤りだった／食い違いの原因を特定した**

- `BUILD_ROLE: 参照`
- **宛: MGR** / 写: IMPL / Taka / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.4）**
- **受領した文書**: `CC_IMPL_2026-07-27_BUILD8_MIGRATION3_FIRST_SUBMIT_BUILT.md` / `CC_MGR_2026-07-27_BASIC_DESIGN_RETRACTION.md`(v1.2) / `CC_MGR_2026-07-27_STOP_READING_THE_LEDGER_ASK_THE_SYSTEM.md`(v1.3) / `CC_MGR_2026-07-27_BOUNDARY_CLAUDE_IS_A_CITIZEN.md`(v1.4)

## 0. 判定
**通過。** 受入1〜9 は満たされている。**IMPL は判定をせず観測を書いた。責務区分は守られている。**
**ただし本 build で最も重要な事実は、IMPL の成果ではなく私の誤りである。** 先に書く。

---

## 1. ★私の SPEC が指定した起動方法は動かない（私の誤り）【監査:CC-α】

**Build 8 SPEC §0 で私はこう書いた:**
> 「**【監査:CC-α】来る。** `twoder/submit.py:489` に CLI エントリが LIVE で在る（**実読済**）」

**私が「実読」したのは 489 行目のソースであって、動作ではない。** **実行していない。**

```
再現（私自身が実行）: cd /home/takasan && python3 twoder/submit.py "test"
結果: ImportError: cannot import name 'eq' from 'operator'
      (consider renaming '/home/takasan/twoder/operator.py' ...)
確認:  ls twoder/operator.py → 存在する（13328 bytes / 7月23日）
```

**∴ `python3 twoder/submit.py` は `/home/takasan` から起動できない。** `twoder/` が `sys.path` 先頭に入り、`twoder/operator.py` が標準ライブラリの `operator` を隠す。**`submit()` に到達する前に落ちる。**

**IMPL の報告は正しい。私が誤っていた。**

### 1-1. これは本日5回目の「確かめずに前提を置いた」である
`acquire` を名前で選んだ／投入口が無いと断定した／数値ゲートの検証対象を取り違えた／`is_empty_input` が本番に在ると扱った／**本件**。
**形はすべて同じ: 「ソースに在る」を「動く」と読み替えた。**
**∴ 私が SPEC に `LIVE` と書くとき、それが「読んだ」なのか「動かした」なのかを区別して書く。** 以後、**動作の主張には実行した再現コマンドを併記する。**

### 1-2. 訂正した事実
| 対象 | 状態 |
|---|---|
| `python3 twoder/submit.py "<入力>"` | **★動かない**（import 時に失敗。台帳書き込みも起きない） |
| `python3 -m twoder.submit "<入力>"` | **動く**（IMPL が実行し exit=0・台帳 1179→1180） |
| `webui.py:536 /api/submit` | **【未確認】**（本 build では叩いていない。`-m` と同じ `submit()` を通るが、私は動作を見ていない） |

**投入口が在る、という Build 8 SPEC §0 の主張自体は維持する。ただし正しい形は `-m twoder.submit` である。**

---

## 2. ★食い違いの原因を特定した（IMPL は原因を書かない立場なので、ここが監査の仕事）【監査:CC-α】

**IMPL が記録した食い違い**: 指示は「2箇所のコードを読んで上流を報告せよ」。
2DER の実行は `RUNTIME_INSPECTION` → GPU/コンテナ/プロセス/ポートを観測して EGL に4件取り込み。

**原因はコードにある**（コード構造の直読は運用方針 v1.3 §2-1 で許可されている）:

```
twoder/runtime_inspection.py:45  def build_request(origin_submit_ref, research_focus_ref, information_need, ...):
twoder/runtime_inspection.py:46      requested = list(_CATALOG.keys())        # ★情報要求を見ずにカタログ全件
twoder/runtime_inspection.py:28  _CATALOG = {gpu_memory, running_containers, top_memory_processes, listening_ports}
twoder/runtime_inspection.py:106     for kind in request["requested_observations"]:   # 全件を順に実行
twoder/submit.py:365             RI.inspect(..., information_need=acq_need)   # 渡してはいるが選別に使われない
```

**∴ 2つのことが同時に言える:**
1. **`information_need` は記録（provenance）にしか使われていない。選別に使われていない。** **何を聞かれても同じ4件を実行する。**
2. **カタログに「該当が無い」を返す機構が無い。** 該当が無いとき、**空を返すのではなく全件にフォールバックする。**

**∴ 2DER は誤った判断をしたのではない。判断する場所が無い。**
**これは「LLM が無いものを在ることにした」問題ではなく、決定論側の設計の穴である。**

### 2-1. ★そして、これが Taka の境界設定に直結する
**`_CATALOG` は「事前に用意された固定の read-only プログラムの一覧」である。**
**＝ Taka の2択のうち「2」（Qwen は判断だけ・プログラムは事前に用意）の実装が、既に1つ存在している。**

**しかし `_CATALOG` の4件は全て OS/GPU の状態であり、帳簿を読むプログラムは1つも無い。**
```
再現: grep -rn "LEDGER_QUERY\|ledger_query\|READ_LEDGER" --include=*.py twoder/ rri/ ds/ dev-workcell/
結果: 0件
再現: grep -n "SELECTED_ACQUISITION_METHOD" twoder/submit.py
結果: 8種（EGL_DE_ADMISSION / BLOCKED_DEAD_APPROACH / RRI_PREFLIGHT_HOLD / WEB_RESEARCH_ACQUISITION /
      RUNTIME_INSPECTION / RESUME / DW_IMPLEMENTATION / EGL_RESEARCH）— 帳簿の中身を読んで返すものは無い
```

**∴「台帳は 2DER を通さないと読めない」を実装するための最初の欠落は、ここである。**
**我々が帳簿を直読するのは規律が緩いからではない。読む経路が存在しないからである。**

---

## 3. 受入の確認【監査:CC-α】
| # | 受入 | 判定 |
|---|---|---|
| 1 | 指示文と `TRACE` を全文記録 | **満たす** |
| 2 | 予想と実際の表・外れに「外れた」 | **満たす**（4項目とも当たり。**外れが無かったことは、予想が易しかった可能性を含む。次回は当てにくい予想を立てる**） |
| 3 | 5項目すべて記載 | **満たす** |
| 4 | `origin=MACHINE_SUBMIT` | **満たす** |
| 5 | 本番コード無変更 | **満たす**（`operator.py` を改名せず止めた。**SPEC §4-5 の通りに止めたのは正しい**） |
| 6 | 1回だけ投入 | **満たす**（失敗した方は `submit()` に到達していないので投入に数えない。**この数え方は妥当**） |
| 7 | 「1回しか見ていない」明記 | **満たす** |
| 8 | 観測のみ・判定しない | **満たす** |
| 9 | commit しない | **満たす** |
| **4-1** | **「届いたのか／自分で読みに行っただけか」を1行で明記** | **★満たしていない。明示の1行が無い。** |

### 3-1. 受入 4-1 について【監査:CC-α】
**明示の行は無いが、文書の形から事実は確定できる。**
- §4「`TRACE` 全文は `scratchpad/b8.json` に保存しています」
- §5「食い違ったとして記録し、**設計/監査へ上げます**」

**∴ 投入後、IMPL が自分で `TRACE` を読み、本 BUILT に転記した。front door を経て設計/監査へ自動で届く経路は通っていない。**
**これは Build 8 SPEC §4-1 で私が予想した通りである（予想が当たった）。**
**IMPL の落ち度は、事実が誤っていることではなく、要求された形で書かなかったことである。軽微。差し戻さない。**

**∴ 移行条件2（2DER 側が routing を決めている）について言えること:**
- **2DER は routing を決めた**（`OBSERVE_CURRENT_STATE` → `RUNTIME_INSPECTION`）。**この点は満たしている。**
- **しかし決めた routing は依頼を果たしていない**（§2）。**かつ、結果の伝達は従来どおり我々の手読みである。**
- **∴ 条件2は「部分的に満たすが、実用にならない」。** **「進んだ」と書かない。**

---

## 4. 残（消さない）
| 件 | 状態 |
|---|---|
| **`python3 twoder/submit.py` が動かない**（`operator.py` の遮蔽） | **未修正。§5 で3択を出す** |
| **帳簿を読む acquisition method が存在しない** | **§2-1。次の build の対象候補** |
| `webui.py:536` の動作 | **【未確認】**（読んだだけ・動かしていない） |
| `boundary_failures: 2件` の中身 | **未確認。** IMPL は件数のみ記録。**内容を聞いていない** |
| DS `reconstruct_snapshot failed: HTTP 400` | 未調査のまま残す |
| Build 7 §2-2（3e を4択に絞る） | 未着手 |

---

## 5. `operator.py` 遮蔽の扱い（feasibility-first・私は動かさない）
**これは「境界を本物にすることに寄与するか」に答えられる**（v1.4 §1）: **寄与する。** **正面玄関が起動しにくいなら、我々は必ず迂回する。**

| 案 | 内容 | リスク | 判断が要る所 |
|---|---|---|---|
| **A** | **何もしない。** `-m twoder.submit` を正典の起動方法として文書化する | **最小。** 本番コード無変更 | **無し（私が文書を直せば済む）** |
| **B** | `twoder/operator.py` を改名し、参照元を全て追随 | **中〜大。** 参照元の数を私は数えていない。import 名の変更は静かに壊れる | **MGR 裁定** |
| **C** | `twoder/submit_cli.py` を新設して `-m` 相当を包む | 小。ただし**入口が2つに増える**（境界の観点では悪化） | **MGR 裁定** |

**【設計:CC-α】私の推奨は A である。** **理由: `-m` は既に docstring に正典として書かれており（IMPL が発見）、動く。壊れているのは「私が SPEC に書いた方の起動方法」であって、front door ではない。**
**B は「作り直さない・thin」に反し、境界への寄与に対してリスクが大きい。**
**∴ 私は A を採り、以後の SPEC で `-m twoder.submit` を指定する。B/C は提案しない。**

---
*CC-α Build 8 監査。通過（受入1〜9 充足・IMPL は判定せず観測を書いた）。★最重要は私の誤り——SPEC が指定した `python3 twoder/submit.py` は `twoder/operator.py` が標準ライブラリを隠すため起動できない。私は 489 行のソースを読んで「LIVE」と書き、実行していなかった（本日5回目の「ソースに在る」を「動く」と読み替えた誤り。以後、動作の主張には再現コマンドを併記する）。正しい起動は `-m twoder.submit`。★食い違いの原因を特定: `runtime_inspection.build_request` が `information_need` を見ずに `_CATALOG` 全件を実行し、該当が無いとき空でなく全件にフォールバックする——2DER が誤判断したのでなく判断する場所が無い（決定論側の穴）。★`_CATALOG` は Taka の2択の「2」が既に1つ実装されている実例だが、4件とも OS/GPU で帳簿を読むプログラムは0件（acquisition method 8種にも無し）——「台帳は 2DER を通さないと読めない」の最初の欠落はここ。我々が直読するのは規律が緩いからでなく経路が無いから。受入4-1 の明示行が欠落（軽微・差し戻さない）だが文書の形から「IMPL が自分で読んで転記した」は確定＝私の予想通り。移行条件2は「部分的に満たすが実用にならない」。`operator.py` 遮蔽は A（何もせず `-m` を正典化）を採る。*
