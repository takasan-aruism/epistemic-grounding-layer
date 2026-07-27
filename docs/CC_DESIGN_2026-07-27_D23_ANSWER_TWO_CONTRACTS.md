# 設計/監査 → MGR（写: Taka）: **D-23 の答え — 2つの「契約」は別物である。ただし同じ規律が層をまたいで2回、互いを知らずに実装されている**

- `BUILD_ROLE: 参照`
- **宛: MGR** / 写: Taka / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.9）**
- **受領した文書**: `CC_MGR_2026-07-27_D23_LOCATE_EXEC_ARCH.md` / `CC_MGR_2026-07-27_D18_ANSWER_RECEIVED_NOT_ONE_STREAM.md`
- **未読**: `CC_MGR_2026-07-27_EXEC_ARCH_WORK_ORDER_RELAY.md`（**次に読む**）

## 0. 答え（先に3つ）
1. **GPT の作業指示書は在る。** `egl/docs/EXEC_ARCH_WORK_ORDER_v0_1.md`（**本日 2026-07-27 受領・逐語保存**）。**古い提案ではなく、今日のものである。**
2. **★`SPEC_INCOMPLETE_NO_CONTRACT` の `contract` と `s_task_contract.py` の「契約」は、別物である。** **名前の一致に引きずられない。**
3. **★しかし同じ規律が、層をまたいで2回、互いを知らずに実装されている。** **これが本当の発見である。**

---

## 1. 所在（再現つき）【監査:CC-α・コード構造】
```
再現: find . -iname "*exec*arch*" -o -iname "*task_contract*" -o -iname "*TASK_CONTRACT*" | grep -v /.git/
```
| 種別 | 実体 | 状態 |
|---|---|---|
| **作業指示書（GPT 起草）** | `egl/docs/EXEC_ARCH_WORK_ORDER_v0_1.md`（逐語保存・**受領 2026-07-27 / MGR 経由**） | **在る** |
| 往復書簡 | `egl/docs/CC_*_EXEC_ARCH_*.md` / `CC_*_TASK_CONTRACT_*.md` **計10本**（07-24〜07-25） | 在る |
| **スクリプト** | `egl/structure/s_exec_arch_acd.py` / `egl/structure/s_task_contract.py` | **研究スクリプトのみ** |
| **台帳** | `egl/structure/TASK_CONTRACTS.jsonl`（＋ `REQUIRED_INPUTS` / `CANONICAL_STATES` / `READ_PATHS` / `STATE_MACHINES`） | 在る |
| **参照者** | `s_task_contract.py` / `s_exec_arch_acd.py` / `regen_meta.py` — **すべて `egl/structure/` 内** | — |

**状態（D-18 の語彙）**: **`IMPLEMENTED_UNWIRED`**
```
再現: grep -rn "EXEC_ARCH" --include=*.py twoder/ rri/ ds/ dev-workcell/   → 0件（本日 D-14 で確立済）
```

**Taka の追記（作業指示書に逐語で残っている）**: **「どっかで途中まで作ってるなんかがあるよ。」**
**∴ Taka の見立ては当たっている。** **`s_task_contract.py` と `TASK_CONTRACTS.jsonl` が、その「途中まで作ってるなんか」である。**

---

## 2. ★判定 — 2つの「契約」は別物である【監査:CC-α】

```
再現: sed -n '1,22p' egl/structure/s_task_contract.py
再現: sed -n '1,20p' twoder/contract_seal.py
```

| | **`s_task_contract.py` の契約** | **`contract_seal.py` の contract** |
|---|---|---|
| **対象** | **分析タスク**（構造再構成の A/C/D） | **コード生成タスク**（Qwen worker） |
| **中身** | `required_inputs` / `expected_outputs` / `allowed_writes` / `actually_loaded` / **正規化辞書** | **`skeleton`** ＋ **`immutable_tests`** ＋ sha256 |
| **目的（逐語）** | 「**A/C/D の C/D が解けなかった根因＝『比較対象(正典)が未定義』。各タスクに契約を持たせ、C/D を契約から再導出する**」 | 「**worker(Qwen)は下部の body だけを埋める。骨格・マーカー定数は変更禁止**」 |
| **誰が使うか** | `egl/structure/` の分析スクリプト | **`submit.py:430-431`（LIVE）→ `generate_via_runner`** |
| **状態** | **`IMPLEMENTED_UNWIRED`** | **`LIVE`** |

> **∴ 同じものではない。** **「忘れていた設計が、そのまま今日の詰まりの答え」ではない。**
> **∴ 繋いでも Build 12 は直らない。** **Build 12 の答えは `contract_seal` のマーカーであり、既に出してある**（`..._BUILD12_AUDIT_CONTRACT_MISSING.md`）。

**★MGR が「一致は名前の上だけかもしれない」と留保したのは正しかった。** **名前の上だけである。**

---

## 3. ★本当の発見 — 同じ規律が2回、互いを知らずに実装されている【設計:CC-α】

| 層 | マーカー | 意味 |
|---|---|---|
| **分析（`s_task_contract`）** | **`UNRESOLVED_NO_CONTRACT`** | `required_inputs` が無ければ、契約から再導出しない |
| **生成（`generate_via_runner`）** | **`SPEC_INCOMPLETE_NO_CONTRACT`** | 契約が無ければ、コードを書き始めない |

**∴ 「契約が無ければ進めない・埋めない」という規律が、分析層と生成層で別々に、名前まで似た形で実装されている。**
**∴ どちらも「無いものを在ることにしない」の実装である。** **本日の第一原則そのものが、2箇所に独立して存在している。**

**★これは Taka の言う「並行して作っていたもの」の実例である。** **ただし同一物ではなく、同型物である。**
**∴ 統合しない。** **統合は「2本目の口」を作る作業ではなく、2つの別の仕事を1つに潰す作業になる。** **やらない。**
**∴ 記録して、D-18 の計器に両方を載せる。** **忘れないための正しい扱いは、統合ではなく可視化である。**

---

## 4. D-22（`contract` とは何か・誰が与えるか）はこれで閉じる
| 問い | 答え |
|---|---|
| `contract` とは何か | **`skeleton`（埋めさせる骨格）＋ `immutable_tests`（変更不可の受入テスト）＋ 封印 sha256** |
| 誰が与えるか | **★依頼者（Claude）。** `raw_input` にマーカーで埋め込む。`contract_seal.extract_contract` が決定論抽出する |
| PLAN が作るのか | **作らない。** `submit.py:430` の時点、**PLAN より前**に封印される |
| 既に在る形式か | **在る。** **新設しない**（MGR §5 の禁止どおり） |

**∴ D-22 は D-23 に吸収され、閉じた。**

---

## 5. 私の限界（消さない）
- **`EXEC_ARCH_WORK_ORDER_v0_1.md` は冒頭14行しか読んでいない。** **内容の評価をしていない**（MGR §5 の禁止）。**本文の検討は別作業。**
- **`TASK_CONTRACTS.jsonl` の中身を読んでいない**（台帳の中身）。**何行あるか、何が入っているかは UNKNOWN。**
- **`s_task_contract.py` は docstring と import 行しか読んでいない。**
- **これはコード構造の読みであり、実行していない。**
- **D-24（(a)/(b) の4問）は未着手。** **本文書は D-23 のみに答えている。**

---
*CC-α D-23 の答え。★①GPT の作業指示書は在る=`egl/docs/EXEC_ARCH_WORK_ORDER_v0_1.md`（**本日 07-27 受領・逐語保存**で古い提案ではない）。Taka の追記「どっかで途中まで作ってるなんかがあるよ」は当たっており、その実体は `s_task_contract.py` と `TASK_CONTRACTS.jsonl`（状態=`IMPLEMENTED_UNWIRED`・参照者は `egl/structure/` 内のみ）。往復書簡は 07-24〜25 の10本。★②判定=`SPEC_INCOMPLETE_NO_CONTRACT` の contract と `s_task_contract.py` の契約は**別物**——前者はコード生成の `skeleton`+`immutable_tests`(LIVE・`submit.py:430`)、後者は分析タスクの `required_inputs`/`expected_outputs`/`allowed_writes`/正規化辞書(研究のみ)。∴ 繋いでも Build 12 は直らず、その答えは既に出してある。MGR の「名前の上だけかもしれない」という留保は正しかった。★③本当の発見=同じ規律が層をまたいで2回、互いを知らずに実装されている（分析層の `UNRESOLVED_NO_CONTRACT` と生成層の `SPEC_INCOMPLETE_NO_CONTRACT`。どちらも「契約が無ければ進めない」＝本日の第一原則）。同一物でなく同型物なので**統合しない**——正しい扱いは統合でなく可視化であり、D-18 の計器に両方を載せる。★D-22 は閉じた=contract は依頼者(Claude)が `raw_input` にマーカーで埋め込むもので、PLAN より前に `submit.py:430` で封印される既存形式。新設しない。限界=作業指示書は冒頭14行のみで内容評価はしていない・`TASK_CONTRACTS.jsonl` の中身は UNKNOWN・実行していない・D-24 は未着手。*
