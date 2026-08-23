# System Operations Domain / Runtime Management ―― Phase 1 全件調査と仕様のブラッシュアップ v0.1

発: System Operations Domain Manager（Claude / instance=ESDE_AUDIT ★担当変更後の初回）
宛: Taka・MGR
根拠: Taka 指示 2026-08-24「あなたもともと DW 担当だったけど変更ね。詳細は GPT から。
これを読んで現実論を全件調査してブラッシュアップするように」
仕様: `2DER System Operations Domain — GDW / Runtime Management 仕様 v0.1`（§16 Phase 1 = 全件調査・**新規実装0**）
台帳: `ITEM-2DER-EVO-0102`

**★本書は実装0行。★1バイトも動かしていない。★調査と、仕様のどこを現実に合わせるかの提案のみ。**
**★なぜ .md か**: 仕様1本ぶんの分量を入れる口が台帳に無い（`status_note` は1行）。
その口ができるまでの暫定であり、台帳には本書への指し先だけを置く。

---

## 0. 結論を先に（★4行）

1. **仕様が「新設する」としている物の多くは、既に在る。** 新語・新台帳を足す前に、
   `authority.TIERS` / `last_seen_by_key` / `include_gate` / `pending_actor` を当てるべき。
2. **Runtime Manager は在らない。★但し名前だけ在る** ―― `twoder/runtime_supervisor.py` は
   **別物**（1回の LLM 呼び出しのリトライ外皮）。混同すると「在る」と誤読する。
3. **★最大の制約 = いま 2DER は 自分を再起動できない。** 起動/停止/再起動は
   コードから **1箇所も行われておらず**、`authority` が `IRREVERSIBLE / REQUIRES_APPROVAL` として
   明示的に止めている。**Runtime Manager の中核能力は Taka 裁定なしには成立しない。**
4. **§15（私の過去作業の分解）から、決定論化できる Worker が 7 本 抽出できた。**
   どれも本日 私が実際に手で回した手順であり、発明ではない。

---

## 1. 調べ方（鍵）

- 対象 = `ds` / `rri` / `egl` / `dev-workcell` / `twoder` の全 `.py` `.sh` `.md`（`experiments/` 除く）
- systemd は **user と system の両スコープ**を見た
  （★1回目は user だけで数えて `twoder-status` を「不在」と誤判定した。★鍵を狭めた私の誤り）
- 「在る」の判定は **呼び手が居るか**まで見る（★置いてある ≠ 働いている）

---

## 2. Runtime の現実（実在 vs 名前だけ）

| 名指しされている名前 | 実在 | 状態 |
|---|---|---|
| `twoder-webui` | 在り(user) | active |
| `twoder-manager` | 在り(user) | active |
| `twoder-route-worker` | 在り(user) | active |
| `twoder-status` | 在り(system・static) | inactive |
| `workcell-probe` | 在り(system・static) | inactive |
| `workcell-runner@` | 在り(system・template) | ― |
| **`twoder-manager-v0`** | **★不在** | ★本日 CC_ALPHA が既に修理済（下記） |
| **`twoder-file-census`** | **★不在** | 参照は文書のみ |
| **`workcell-deploy`** | **★不在** | 参照は bootstrap script |

**★仕様 §12 が例に挙げた事故は実在した。★但し 2026-08-24 に既に直っている。**
`.claude/hooks/2der_status.sh:164` に逐語で残っている:

> `twoder-manager-v0` は systemd に 無い ∴ ★常に inactive が返り、
> ★常駐が active でも 毎回『誰も起こさない=永久停止』を出していた(★偽陽性)。

∴ **仕様は「これから作る Runtime Manager が防ぐ」と書いているが、実際には
人（CC_ALPHA）が本日 手で直した。★これは Worker 化の第一候補である**
（後述 W8 = 名乗った service 名が引けるかの検査）。

---

## 3. 仕様の各節 × 現実

| 節 | 仕様の要求 | 現実 | 判定 |
|---|---|---|---|
| §7 runtime state 7語 | STOPPED/STARTING/RUNNING/DEGRADED/STALLED/FAILED/QUARANTINED | 既存は `FAILED` のみ（8ファイル・★但し TASK の FAILED）。他5語は **0** | **新語5つが要る**。仕様の「TASK と分離」は正しい |
| §10 3段の門 | SAFE / CONTROLLED / ESCALATE | **`authority.TIERS` に既に3語**: `OBSERVE` / `REVERSIBLE` / `IRREVERSIBLE`。決定は `AUTO_EXECUTE` / `REQUIRES_APPROVAL` / `AUTO_ROLLBACK`。表は **25項目** | **★新語0で足りる。仕様の語を捨てて既存に寄せる** |
| §8 自己申告禁止 | 外から観測する | **既に規律。** `last_seen_by_key` が event_trace から key ごとの最終時刻を出す（自己申告0） | **★流用できる** |
| §9 restart | heartbeat timeout → restart | **★コードに起動/停止/再起動が 1箇所も無い。** `systemctl` の出現は 全部 *禁止リスト* か read-only `show` 1件 | **★不可。裁定が要る**（下§5） |
| §13 台帳 | 新台帳を作らず既存で | 既存候補: `failure_recurrence` / `human_escalation_ledger` / `approval_registry` / DW の finding | **★足りるか未検証（UNVERIFIED）**。Phase 2 で当てる |
| §6 Runtime Manager | 新設 | **★存在しない。** `runtime_supervisor.py` は **名前が似た別物** | **★新設が要る。★但し名前を変える**（下§4） |
| §3 OBSERVE→…→LEARN | Domain Manager の一周 | `manager_v0`(1002行) が OBSERVE→DISPATCH の骨格を持つ。`route_worker` が自己点検を回す。`include_gate` が重なりを止める | **★半分在る。** 欠けは CLASSIFY / COMPARE / LEARN |
| §4 Worker 4種 | Performance/Resource/Integrity/Regression | 「Worker」を名乗る物は在るが **LLM を呼ぶ実装 Worker**（`qwen_worker` 等）で、**診断 Worker は 0** | **★新設。★但し中身は本日の私の手順**（§6） |

---

## 4. ★名前の衝突（先に潰すべき1点）

```
仕様の「Runtime Manager」   = Manager/Worker という★実行主体の生死を管理する
既存の runtime_supervisor.py = ★1回の LLM 呼び出しのリトライ外皮
```

`runtime_supervisor.py` の逐語（docstring）:

> **Hard boundaries: NO model change, service restart, GPU/serve-config change, systemd, sudo.**

**∴ 既存は「systemd を触らない」ことを設計として宣言している。**
新しい Runtime Manager をこの名前の近くに置くと、**後から読む者が必ず取り違える。**
★提案: 名前を **`runtime_manager`** ではなく、責務が読める語にする
（例 `actor_liveness` / `process_registry`）。★決めるのは Taka か MGR。

---

## 5. ★★最大の制約 ―― いま 2DER は自分を再起動できない

実測:

```
コードから systemctl を叩く所 = ★0（起動/停止/再起動）
  authority.py:39   "KILL_OR_RESTART": (REQUIRES_APPROVAL, "... systemctl restart", IRREVERSIBLE)
  authority.py:57   _MUTATING_HEADS = {"systemctl": "KILL_OR_RESTART", ...}
  dw/executor.py:48 forbidden_base_commands = ['sudo','rm','shutdown','reboot','systemctl',...]
  build_planner.py:64 DESTRUCTIVE_MARKERS に "systemctl"
唯一の例外 = frontdoor_profile.py:43 の `systemctl --user show`（★read-only）
```

**∴ 仕様 §9 の「安全なら restart」は、いまの門では 1回も通らない。**
本日 webui / manager / route-worker を再起動したのは **すべて私（人の手）** である。

**★Taka の裁定が要る（3択・私の推薦は B）**

| | 案 | 意味 |
|---|---|---|
| A | Runtime Manager に restart を許す | `authority` に新しい行を足す。★門の意味が変わる（IRREVERSIBLE を機械が通す） |
| **B** | **Runtime Manager は「観測と上申」まで。restart は既存の承認経路（`approval_registry`）を通す** | **★門を変えない。★Claude は消えるが Taka の承認は残る** |
| C | 対象を限定して許す（webui は不可・Worker プロセスだけ可） | 中間。★「どれが安全か」を誰が決めるかが新しい問いになる |

**★これが決まらないと §9 と §16 Phase 4 は書けない。**

---

## 6. ★§15 ―― 私の過去作業を Manager 判断 / Worker 実働へ分解した

対象は仕様指定の全件（EVO-0096 / 0097 / 0101 / front door 性能 / event_trace /
計器偽陽性 / 回帰異常 / 自分の測定事故）。

### 6-1 分解表

| 案件 | OBSERVE | DETECT | CLASSIFY | COMPARE | JUDGE | 実働 | VERIFY |
|---|---|---|---|---|---|---|---|
| EVO-0096 台帳増加 | 機械 | 機械 | 機械 | 機械 | **人** | 機械 | 機械 |
| EVO-0097 全量list | 機械 | 機械 | 機械 | 機械 | **人** | 機械 | 機械 |
| EVO-0101 並列化 | 機械 | 機械 | 機械 | 機械 | **人** | 機械 | 機械 |
| EVO-0098 回帰4本 | 機械 | 機械 | 機械 | 機械 | **人** | 機械 | 機械 |
| 計器偽陽性(unit名) | 機械 | 機械 | 機械 | ― | 機械 | 機械 | 機械 |
| 私の測定事故3件 | 機械 | **機械化できる** | 機械 | 機械 | ― | ― | ― |

**★読み方**: OBSERVE〜COMPARE と VERIFY は **全部 機械にできた**。
**人が要ったのは JUDGE の1点だけ** ―― 「畳む/束ねる/別プロセスにする/仕様と試験のどちらが正しいか」。
**∴ Claude を減らす道は『JUDGE 以外を全部 Worker にする』で正しい。**

### 6-2 ★抽出できた Worker（★全部 本日 私が実際に手で回した手順・発明ではない）

| # | Worker | 入力 | 出す事実 | 本日どこで効いたか |
|---|---|---|---|---|
| **W1** | **SCAN_COUNTER** | 口の名前 | その口が入力を **何回 全走査したか** | 6回→2回、その後 **11回**だったと判明（★私の数え落としを機械が捕まえる） |
| **W2** | **STEP_TIMER** | 節 | **段ごとの秒** | `7_tail 113.26秒` を1発で特定（★読んで探すのをやめられた） |
| **W3** | **OUTPUT_EQUIVALENCE** | 旧版・新版・同じ入力 | **欄ごとの一致/不一致** | 31欄中30欄一致 / 7欄中6欄一致。★入力を **書込禁止**にする（後述） |
| **W4** | **FIRST_BAD_COMMIT** | 試験名 | **いつから落ちたか（1 commit）** | EVO-0098 の犯人を `7b025de` に確定（24点で） |
| **W5** | **GROWTH_PROBE** | 台帳一覧 | metadata だけで **増加率** | 107本中 増えるのは3本 と確定 |
| **W6** | **DUPLICATION_RATE** | 台帳 | **内容が同一の行の割合** | 78.3% → 37.3%。★負荷に依存しない効果指標 |
| **W7** | **KEY_GUARD** | 報告文 | 数に **鍵（環境・同時実行数・窓）** が在るか | ★本日 私が3回 落とした所 |
| **W8** | **NAME_RESOLVES** | 名乗った service / id | **引けるか** | `twoder-manager-v0` の偽陽性型 |

### 6-3 ★Worker を作る時に必ず要る2つの規律（★本日 実測で判明）

1. **★入力を書込禁止にする。**
   `_use()` が走査のたび etrace へ書き足すため、**同じ入力のはずが伸びる**。
   実測: 個別呼び12回走査の間に `handed` の count が **189 → 188** とずれた。
   `chmod 444` にしたら **完全一致**。★これを入れないと OUTPUT_EQUIVALENCE は嘘をつく。
2. **★負荷に依存する指標を効果の証拠にしない。**
   秒 / MB/日 / RSS は「その時 誰が同じ資源を使っていたか」で変わる。
   ★効果は **走査回数・重複率・処理行数** で判定する。

---

## 7. ★仕様のブラッシュアップ提案（差分だけ）

| 節 | 現仕様 | ★提案 | 理由 |
|---|---|---|---|
| §10 | SAFE / CONTROLLED / ESCALATE を新設 | **`authority.TIERS`（OBSERVE / REVERSIBLE / IRREVERSIBLE）に寄せる** | 既に25項目の表が動いている。新語0 |
| §6 | 名前 = Runtime Manager | **別の名前にする** | `runtime_supervisor.py` と取り違える |
| §8 | heartbeat を新しく取る | **まず `last_seen_by_key` で足りるか測る** | 自己申告0の既存計器。★足りない分だけ足す |
| §9 | 安全なら restart | **★裁定が先**（上§5） | いまの門では1回も通らない |
| §13 | 既存台帳で表現可能か調査 | **★Phase 2 の最初の仕事に固定する** | 本書では未検証（UNVERIFIED） |
| §15 | 過去作業を分解 | **★完了（§6）。Worker 8本を抽出** | ― |
| §16 | Phase 2 で最小一周 | **★Phase 2 は W1〜W4 だけで始める** | 本日 実測で効いた4本。★4種の Worker 分類は 実績が出てから決める |
| ― | ― | **★追加: 「入力を書込禁止にする」を Worker の共通規律に書く** | 入れないと検証が嘘をつく（§6-3） |

---

## 8. ★私がしていないこと

★実装 0 行 ／ 新台帳 0 ／ 新 state 0 ／ 新 ID 0 ／ service を1つも起動・停止していない
★`authority` を触っていない ／ `runtime_supervisor.py` を触っていない
★本書の内容で 2DER の挙動を1バイトも変えていない。

## 9. ★次に要るもの（★Taka / MGR へ）

1. **§5 の3択の裁定**（Runtime Manager に restart を許すか）― ★これが最優先。決まらないと Phase 4 が書けない
2. **§4 の名前**（Runtime Manager をどう呼ぶか）
3. **Phase 2 の範囲**: 私の推薦は **W1〜W4 の4本を Worker として立て、EVO-0096/0097/0098/0101 を
   再現できるか（★同じ結論に機械だけで到達できるか）を試金石にする**
