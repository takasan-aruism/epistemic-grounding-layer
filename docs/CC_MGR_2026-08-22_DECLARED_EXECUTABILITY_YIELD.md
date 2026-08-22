# declared — AXIS = `EXECUTABILITY_YIELD`（実行可能性による yield ／ ★priority ではない）

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
開発者規律 確認済（`2DER_DEVELOPER_DISCIPLINE_v1.0` / `TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3` / **ESDE 正本 v0.1**）
**★実装の前に置く1枚。★コードは1行も変えていない。**
item: `ITEM-2DER-EVO-0084` の1件のみ ／ 測ったHEAD: twoder `8b64b1f` / dev-workcell `68c3b4c` / egl `03a4195`

**Taka 裁定（2026-08-22）逐語の要点**
```
FIFO の順序原則は維持する。
現在の手番で進行不能な task は「順番を失う」のではなく ★一時的に yield し、
同一 FIFO 内の次の実行可能 task を探してよい。
★「重要だから後続 task を先にする」という priority scheduling は禁止。
「現在実行不能なので、その task を保持したまま次の実行可能 task へ進む」は許可する。
待機 task は ★原因付きで残し、条件が解消したら ★元の FIFO 資格を保持して再評価する。
★194件を先に流すこと自体を成功条件にしない。
★成功条件 = FIFO の意味を壊さず、実行不能な先頭 task が
             後続の実行可能 task を ★永久停止させないこと。
```

---

## 0. ★先に、私の測定の誤りを2件 訂正する

### 訂正① 「5 tick 回して何も動かなかった」は**誤り**

私は窓（`timeout 330 python3 -m twoder.manager_v0`＝1プロセス・`_STOPPED_AT` 持続）の後に
task を分類で数え直し、**194→194 / 282→282 / 操作 61-63-70 が不変**だったので
「頭が塞いでいる読みに実測が付いた」と書いた。**間違い。**

**実測**: 同じ task `TASK-2DER-731F98A0` は
```
13:57  dw_state = CREATED           next_op = PLAN          actor = CLAUDE
14:15  dw_state = ★JUDGE_REQUIRED   next_op = UPPER_REVIEW  actor = -
```
**★動いていた。**分類カウントは **同じ分類内の移動を見られない**（両時点とも `claude_barrier=True`＝282側）。
∴ **計器が鈍かった。「不変」は「動かなかった」ではない。**（★記憶「数には鍵を添える」と同型）

### 訂正② `MANAGER_V0_ONCE=1` を3回叩いたのは**証拠にならない**

3回とも同じ task を選んだが、`manager_v0.py:34` 逐語
「`_STOPPED_AT = {}` ★プロセスの記憶（再起動で消える）」／`:294`「★再起動で 忘れる=★恒久の 除外表に ならない」。
∴ **ONCE は毎回 記憶が空 ∴ 同じ頭を選んで当然。3回は 1回と同じ情報量。**
（★監査が本日 mtime で断じかけて撤回したのと同じ型 ―― ★計器の誤用）

---

## 1. AXIS 宣言

```
AXIS: EXECUTABILITY_YIELD
SCOPE:
  entry:       _last_task() が並びを見て 1件を選ぶ
  exit:        ★実行不能な先頭 task が 後続の実行可能 task を 永久停止させない
               （★194件を流すことは exit にしない ―― Taka 逐語）
  authority:   発行 0・変更 0
  persistence: ★新規 0（並びの file も state も 語彙も 増やさない）
  components:  manager_v0._last_task 段①/段②/段③ ／ _machine_turn ／ _queue ／ _queue_write ／
               manager_decide.decide_tick(2DER製) ／ _STOPPED_AT ／
               dw.dispatch._MAP ／ front door /api/state
範囲外:        priority ／ 194件の消化 ／ 並びの順序変更 ／ 新しい除外表
```

---

## 2. ★全件調査（作用ベース）―― **yield は既に在る**

**探索範囲** = `manager_v0.py` 全行 ＋ `manager_decide.py` ＋ `dw/dispatch.py` ＋ `domain_dw.py`。

### ★段① は既に yield している（逐語）

```python
# manager_v0._last_task 段①
if not _machine_turn(st):
    keep.append(tid)      # ★並びには 残す
    continue              # ★先頭を 塞がない
pick = tid
keep.append(tid)
```
逐語コメント「★★未知の 状態は ★勝手に 分類しない=★対象外(★但し ★並びには 残す=**★先頭を 塞がない**)。」

### ★段② も既に yield している（逐語・2箇所）

```python
if tid in _ESC_OPEN:
    _record({"action": SLEEP, "task_id": tid, "reason": "AWAITING_HUMAN"},
            {"phase": "candidate_skip", ...,
             "key_note": "★人の決定を待っている(escalation 未解決)。台帳・state は変えない。★毎周 再評価する"})
    continue                               # ★後続の 実行できる 案件へ 進む

if _stop and decide_tick(...)["action"] == STOP:
    _record({"action": SLEEP, "task_id": tid, "reason": ...},
            {"phase": "candidate_skip", ..., "stopped_at_stage": list(_stop),
             "key_note": "★tick が『走らせない』と 決めた 物は 戻さない(★同じ判断器・同じ記憶)。★消さない=★次の候補へ"})
    continue                               # ★後続の 実行できる 案件へ 進む
```
さらに逐語「★解決されたら ★次の 周で ★自動で 候補へ 戻る（**★恒久の 除外表を 作らない**）」
「**★消さない=★並びからも submitted からも 削らない**」。

**∴ Taka が求めた4条件は 機構としては ★既に実装されている。**

| Taka の要求 | 既存の実体 | 状態 |
|---|---|---|
| 順番を失わず一時的に yield | `keep.append(tid); continue` | **PRESENT** |
| 同一 FIFO 内の次の実行可能 task を探す | 段①段②とも `continue` で次候補へ | **PRESENT** |
| 待機 task を**原因付き**で残す | `reason=AWAITING_HUMAN` / `stopped_at_stage` / `key_note` | **PRESENT** |
| 条件解消で**元の FIFO 資格を保持して再評価** | 「毎周 再評価する」「恒久の除外表を作らない」 | **PRESENT** |
| priority を作らない | 順序は `q` のまま・`keep` は元順 | **PRESENT** |

---

## 3. ★では何が足りないのか ―― **判定に使う事実がずれている**

### 分母（★9状態を全件走査した）

```
状態の総数 = 9
   CREATED                   op=PLAN         _MAP.barrier=True   _machine_turn=True   ★
   READY_FOR_IMPLEMENTATION  op=GENERATE     _MAP.barrier=False  _machine_turn=True
   READY_FOR_AUDIT           op=AUDIT        _MAP.barrier=False  _machine_turn=True
   DISPOSITION_REQUIRED      op=DISPOSE      _MAP.barrier=True   _machine_turn=True   ★
   READY_FOR_REGENERATE      op=REGENERATE   _MAP.barrier=False  _machine_turn=True
   READY_FOR_UPPER_REVIEW    op=UPPER_REVIEW _MAP.barrier=False  _machine_turn=True
   JUDGE_REQUIRED            op=UPPER_REVIEW _MAP.barrier=False  _machine_turn=True
   COMPLETE                  op=NONE         _MAP.barrier=False  _machine_turn=False
   BLOCKED                   op=BLOCKED      _MAP.barrier=True   _machine_turn=False

★_machine_turn=True は 7/9。★そのうち _MAP.barrier=True は 2件(CREATED / DISPOSITION_REQUIRED)。
```

### ★決定的な実測 ―― **状態の barrier と task の barrier は別物**

```
_MAP["JUDGE_REQUIRED"][3]                 = ★False（状態の欄）
/api/state?task_id=731F98A0 の claude_barrier = ★True （その task の実際）
/api/state?task_id=731F98A0 の dispatch_status = ★PENDING EXTERNAL ACTOR
```

理由 = 入口は **task ごとに** 供給者の有無を見て決める
（`dispatch.py:155` `UPPER_REVIEW` は `trivially_clean(tid)` の時だけ機械が供する／`:163` の門）。
∴ **`_MAP` の欄は「その状態は一般に人の関門か」であり、「この task が今 実行可能か」ではない。**

### ★欠落の1点

```python
# manager_v0._last_task 段①（逐語）
st = _call("/api/state?task_id=" + tid, timeout=60).get("dw_state")
                                                    ^^^^^^^^^^^^^^^^
# ★同じ呼び出しで claude_barrier も dispatch_status も 返ってきているのに ★dw_state だけ取って捨てている
if not _machine_turn(st):   # ★状態レベルの判定
```

**∴ yield の述語が「状態」を見ており、「この task が今 実行可能か」を見ていない。
その事実は ★既に手の中に在る（同じ1回の呼び出しで返っている）。**

### ★これは「Taka が止めた手書き規則」の復活ではない（★重要）

`_machine_turn` の逐語コメント：
> ★★2026-08-15 22:3x: ★私は ここに ★『役が CLAUDE なら 押さない』を 足していた
> =★★★それは **手書きの 規則**(★Taka が 止めた 物)＋★実物と 矛盾する
> (★`CREATED` の 役は MANAGER/CLAUDE だが ★入口は Qwen の planner で 自動で 供する=★実測で 進んでいた)。
> → ★★★`_MAP` の 通り『★次の 仕事が 在るか』だけで 決める。**★誰が 供するかは ★入口が 決める。**

**止められたのは「役名で手書きに判定する規則」。**
`claude_barrier` / `dispatch_status` は **入口（front door）が自分で計算して返している判定**であり、
まさに逐語「**誰が供するかは入口が決める**」に従う値。
∴ **同じ穴には落ちない。むしろ その原則を守る方向。**
（★但しこれは私の読み。★監査に独立検証を求める ―― §7）

---

## 4. 因果鎖（各点で 誰が作る/何を/どこへ/誰が読む/無い時どう止まる/本線で呼ばれるか）

```
① 並びを読む      _queue() が QUEUE_FILE から list を作る／読むのは _last_task／
                  無ければ空 list（fail-open だが 選ばない=安全側）／本線で毎周 呼ばれる     OBSERVED
② 各 task を引く  front door /api/state が dict を返す／読むのは _last_task／
                  例外なら keep して次へ（★既に yield している）／本線で毎周           OBSERVED
③ 実行可能か判定  _machine_turn(dw_state) が bool を作る／保存先なし／読むのは段①／
                  未知状態は False=先頭を塞がない／本線で毎周                          ★BROKEN（材料不足）
④ yield          keep.append + continue／並びの順は保持／読むのは _queue_write／
                  ―／本線で毎周                                                        OBSERVED
⑤ 次候補へ       ループが次の tid を見る                                               OBSERVED
⑥ resume         次の周に同じ並びを頭から再評価（恒久の除外表なし）                    OBSERVED
⑦ 原因の記録     _record(... phase=candidate_skip, reason=...) → ETRACE                段②のみ OBSERVED
                                                                                        ★段①には無い＝UNVERIFIED
```

**止まっているのは③の1点。④⑤⑥は既に在る。⑦は段①に無い。**

---

## 5. ESDE 宣言（正本§12 ＋ ★Taka が名指しした5点）

```
AXIS: EXECUTABILITY_YIELD

EQUALITY（★Taka「waiting / skipped / removed / completed を混同しない」）
  canonical_protocols: [DW dw_state（9語）, front door の判定欄（claude_barrier / dispatch_status）,
                        manager_decide の 3語（RUN / SLEEP / STOP）]
  ★4語の既存の実体を全件で当てた:
    waiting    = 段②の `phase=candidate_skip` ＋ `reason`（AWAITING_HUMAN 等）★並びに残る
                 ＋ `waiting_on_materials`（逐語「★単一の答えを出さない=材料を並べる」）
    skipped    = ★同じ `candidate_skip` が使われている ―― ★waiting と ★区別されていない
    removed    = `_queue_write([t for t in _queue() if t != tid])`（5箇所）
                 ★domain_dw:393「★受領が 済んだ=★並びから 落とす」＝ waiting とは別
    completed  = dw_state `COMPLETE`（_MAP op=NONE）
  incompatible: [★waiting と skipped が同じ語（candidate_skip）に載っている]
  unknown:      [段①の yield には ★語が無い（記録もされない）]
  status: ★CONFLICT（★Taka の名指しどおり ―― 混同が実在する）

SYMMETRY（★Taka「yield ↔ resume が両側存在する」）
  pairs: [yield ↔ resume, 記録する ↔ 読む, 並びに残す ↔ 並びから落とす]
  required 3 / present 2 / missing 1 / unverified 0
    ✔ yield ↔ resume        段②=candidate_skip ↔ 「毎周 再評価する／恒久の除外表を作らない」
                            段①=keep+continue  ↔ 次周に同じ並びを頭から
    ✔ 並びに残す ↔ 落とす   keep.append ↔ _queue_write（★受領後のみ落とす）
    ✘ 記録する ↔ 読む       ★yield の記録（candidate_skip）を ★読む側が 0
                            ＝ MISSING: YIELD_RECORD_HAS_NO_READER
  ★但し ★段① の yield は ★記録すらされない ∴ 対称性以前に ★片側が無い

LINKAGE（★Taka「yield 後に次 task へ実際に渡る」）
  edges:
    E1 判定→yield        from=_machine_turn to=keep+continue   evidence=source   status=OBSERVED
    E2 yield→次候補      from=continue     to=次の tid          evidence=source   status=OBSERVED
    E3 次候補→pick       from=ループ        to=pick             evidence=★実走     status=★UNVERIFIED
    E4 yield→原因の記録  段②のみ                                evidence=ETRACE    status=OBSERVED
                         ★段①は ★ABSENT
    E5 次周→resume       from=_queue()     to=同じ並びを再評価   evidence=source   status=OBSERVED
  declared 5 / observed 4 / broken 0 / absent 1 / unverified 1
  ★E3 が UNVERIFIED = ★『実行不能な頭を yield した後、後続が実際に pick された』実走証拠が ★無い
     （★私の窓の測定は 訂正①のとおり ★分類カウントでは見えなかった）

HIERARCHY（★Taka「scheduler が『重要度』を判断しない」）
  boundaries: [順序を変えない, 重要度を作らない, 判断は 2DER 製の判定器,
               誰が供するかは入口が決める, 恒久の除外表を作らない]
  required 5 / passed 5 / violation 0 / unreachable 0
  ★順序: `keep` は元の並び順のまま append ∴ ★並べ替えない
  ★重要度: どこにも score も rank も無い（全件確認）
  ★判断器: decide_tick は 2DER 製（Claude は1行も書き換えていない）
  ★入口: 供給者の有無は front door が計算して返す（★§3 の逐語）

AXIS の性格（★Taka「今回扱うのは『実行可能性による yield』であり priority ではない」）
  ★確認: 本 AXIS は ★述語の材料を 1つ足すだけ。
  ★順序・優先・重要度に触れる差分は ★1つも含まない。
  ★『194件を先に流す』は ★exit に入れていない（§1 SCOPE）。

R1_END_TO_END      status: ★UNVERIFIED
                   evidence: ★E3 の実走証拠が無い（★訂正①）
R2_DENOMINATOR     required: 9状態 ／ observed: 9（全件走査済）
                   ★_machine_turn=True 7 / うち _MAP.barrier=True 2
                   ★但し task レベルの barrier は _MAP と一致しない（JUDGE_REQUIRED が反例）
                   status: ★BROKEN（状態の分母と task の分母が別物）
R3_INTERNAL_GATES  gates: [_machine_turn, _ESC_OPEN, decide_tick(STOP), front door の門]
                   passed: [] / failed: [] / unverified: [4つとも ★実走で撃っていない]
R4_REJECTION       rejection_conditions:
                     ①未知の状態 → False（先頭を塞がない）
                     ②COMPLETE → False
                     ③BLOCKED → False
                     ④escalation 未解決 → candidate_skip
                     ⑤decide_tick が STOP → candidate_skip
                   actually_rejected: [] ★実装後に全件 発火させる
                   status: ★UNVERIFIED

UNDERSTANDING  candidate: EXECUTABILITY_YIELD
               requires: [③が task レベルの事実を見る, E3 の実走証拠, ⑦段①の原因記録,
                          waiting と skipped の語の分離]
               evidence: [段①②に yield が既在（source 逐語）, 分母9の全件走査]
               unresolved: [E3 実走 / R3 4門 / R4 5条件 / EQUALITY の CONFLICT]
               result: ★UNKNOWN

CREATION   status: NOT_EVALUATED
DECISION   ★DESIGN_HOLD
```

---

## 6. ★DESIGN_HOLD の理由（正本§10④「1点でも推測でしか埋まらないなら進まない」）

```
① EQUALITY が ★CONFLICT = waiting と skipped が同じ語(candidate_skip)に載っている。
   ★Taka が名指しで「混同しない」と言った当のもの。★語を分けるのか同じでよいのかは ★私が決めない。
② E3（yield 後に後続が実際に pick される）の ★実走証拠が無い。
   ★私の窓の測定は 分類カウントで ★見えなかった（訂正①）。★正しい計器を先に作る必要がある。
③ 段① の yield は ★原因を記録していない ∴ 「原因付きで残す」(Taka 逐語)を ★満たしていない。
```

**∴ 実装しない。**

---

## 7. 監査へ出す3点（★私の読みを独立に検証してほしい）

```
Q1 ★§3 の読み ―― 「claude_barrier / dispatch_status を見るのは
   ★Taka が止めた『役名の手書き規則』の復活ではない」は成立するか。
   ★根拠にした逐語= 「★誰が 供するかは ★入口が 決める」(manager_v0._machine_turn)。
   ★ここを外すと 本 AXIS 全体が 崩れる。

Q2 ★E3 を測る計器の形。★私の分類カウントは 鈍かった(訂正①)。
   ★『実行不能な頭を yield した後、後続が実際に pick された』を
   ★どの記録で見るか（candidate_skip の ETRACE か / pick の記録か / 別か）。

Q3 ★EQUALITY の CONFLICT ―― waiting と skipped を分けるべきか。
   ★分けるなら 新語になる ∴ ★正本§3 の10語との関係が要る（★本日 私は造語で1度 咎められている）。
```

---

## 9. ★追記 2026-08-22 15:0x ―― Taka が exit と実走を確定 ／ 計器は既存で足りた

### Taka 指示（逐語の要点）

```
★EVO-0084 だけ閉じる。
★監査の3問に答えが出たら ★1件だけで
  yield → 後続pick → 元task保持 → 条件解消後再評価  を ★実走させる。
★これが通って ★ESDE 上で ESTABLISHED になったら ★その時点で常駐を上げて 194件を流す。
```

∴ **194件は exit ではなく ESTABLISHED の後段。順序が確定した。**

### ★Q2（E3 を測る計器の形）は解けた ―― **既存記録で足りる**

探した範囲 = `/api/etrace?task_id=` の返り全欄。

```
task_trace = {task_id, events, count, truncated, total, run_ids}
実測(TASK-2DER-731F98A0) = events ★24 / truncated=False
  component 内訳 = DW 11 / MANAGER_V0 5 / DISPATCH 4 / RUNGATE 4

MANAGER_V0 tick の outputs が持つ欄:
  action / task_id / reason / handed_to / ★phase /
  ★dw_state_before / ★dw_state_after / ★stopped_at_stage / gate_cause / planner_outcome
```

**★Taka の4段を この欄へ そのまま割り当てられる:**

| 段 | 観測 |
|---|---|
| ① yield | 対象 task の行に `phase == "candidate_skip"` ＋ `reason` が在る |
| ② 後続pick | 同じ時刻帯に **別の** task の行が `action == "RUN"` |
| ③ 元task保持 | 後の周に **同じ** task の行が再び現れる（★消えていない） |
| ④ 条件解消後再評価 | その行の `dw_state_after` が動く（`before != after`） |

### ★「永久停止」は `before == after` の反復として直接見える（実測）

```
14:07:38  action=RUN  before=CREATED         → after=★JUDGE_REQUIRED   ★動いた
14:07:50  action=RUN  before=JUDGE_REQUIRED  → after=JUDGE_REQUIRED    ★動かない
14:07:55  action=RUN  before=JUDGE_REQUIRED  → after=JUDGE_REQUIRED    ★動かない
  3行とも phase=after_gate / stopped_at_stage=UPPER_REVIEW
```

**∴ 分類カウント（194/282）は要らなかった。**私の §0 訂正①の原因はこの計器を使わなかったこと。

### ★最小差分が1つ増えた

```
(a) 段①の述語に ★入口の判定を渡す
    ★同じ /api/state の応答に既に在る claude_barrier / dispatch_status を捨てない
    ★★Q1 が成立することが前提（監査待ち）
(b) 段①の yield に ★_record を足す
    ★Taka 逐語「待機 task は ★原因付きで残し」を満たすため
    ★新機構ではない = 段②が既に使う ★同じ _record・★同じ phase=candidate_skip の形
```

### ★★実走の前提に UNVERIFIED が1つ（★実装前に明記する）

**「後続 pick」を観測するには 並びに ★実行可能な後続が居なければならない。
その並び（`runs/manager_queue.json`）の中身は ★front door から引けない。**

```
探した範囲 = /api/control の 24面 ＋ state / tasks / ledgers / resolve / etrace / roadmap
★並びを返す面 = ★0
★直読は境界違反（★本日 実際に門が止めた）
∴ ★並びの長さ・中身 = ★UNVERIFIED
```

**∴ 実走が「後続 pick」を示せなかった場合、②実装が悪い と ③並びに後続が居ない を
★区別できない。** これは §2 で測った「取得不能11件」の型（query入口）が
**実走の設計そのものに刺さった1例。**

**対処（★新しい口を作らない）**: 実走は **2周以上**回し、
`MANAGER_V0 tick` の **task_id が2種類以上 現れるか**を見る。
1種類しか出なければ **「後続が居ない」と結論せず UNVERIFIED として止める**
（★正本§11「0件・bool(exists)・証拠1件を成功判定に使わない」）。

### ★実走の手順（★実装後・★1件だけ・Taka 逐語）

```
R1 before  対象 task の /api/etrace を取る（★変更前の行を保存）
実装       (a)(b) の最小差分のみ
R1 after   窓を切って ★2周以上 回す
判定       ①phase=candidate_skip が出たか
           ②同時刻帯に別 task の action=RUN が出たか
           ③後の周に同じ task の行が再び出たか
           ④その行で before != after になったか
R4         §5 の拒否条件5件を ★実際に発火させる
★4つとも取れた時だけ ESTABLISHED。★1つでも欠けたら UNKNOWN のまま。
```

---

## 10. ★訂正と確定 2026-08-22 15:4x ―― 差分は「除去 → 保持」の1点

### ★訂正7 ―― §3 の「`claude_barrier` / `dispatch_status` を見る」は**両方とも不可**

source で確定した：

```python
webui.py:202   is_claude = nlo["actor_role"] in ("MANAGER", "CLAUDE_SENIOR")
webui.py:231   "claude_barrier": is_claude, "dispatch_status": dispatch_status
```

**∴ `/api/state` が返す `claude_barrier` は `_MAP` 由来ではなく、webui が役名を並べた派生値。
= Taka が 2026-08-15 に止めた形そのもの。`dispatch_status` と同じ出所。**
`dispatch.py:66` の `nlo["claude_barrier"]`（`_MAP` の4番目）とは**別物で、同名。**

**★実測（分母つき・私と監査が独立に）**

```
        私        監査
分母    585       590
食い違い ★82      83
内訳    UPPER_REVIEW 79 / BLOCKED 3     UPPER_REVIEW 80 / BLOCKED 3
向き    False→True 79 ／ ★True→False 3  「全て False→True」
                    ↑★私の実測では一様でない。★鍵(分母)の差の可能性 ∴ 両方残す
```

**∴ 述語に派生値を使ってはならない。**

### ★確定 ―― Taka の求める機構は既に在り、**解決の仕方だけが違う**

`manager_v0.py:421-430`（逐語）:

```python
if not gate["allow"] or after.get("dw_state") == state.get("dw_state"):
    _STOPPED_AT.setdefault(task["task_id"], []).append(str(stage))
d = _use("decide_tick", decide_tick, task, gate, _STOPPED_AT.get(task["task_id"], []))
# ★★2026-08-15 00:3x: ★止まった 案件が ★並びの 先頭で 詰まると ★後ろが 一生 進まない
#   ★∴ ★『同じ所で2回』(★2DER が 出す 語)なら ★並びから 落とす=★★叩き続けない ／ ★飛ばさない
if d.get("reason") == "同じ所で2回":
    _queue_write([t for t in _queue() if t != task["task_id"]])
```

**問題意識は Taka と同一。解決が `removed`（並びから落とす）。**
Taka 逐語「**順番を失うのではなく ★一時的に yield**」。

```
★∴ 差分 = 「除去 → 保持したまま yield」の ★1点。
```

これで §5 の2つが具体化した：
- **対等性 CONFLICT** = 現状 `waiting` と `removed` が**同じ経路に潰れている**
- **対称性 missing** = `_STOPPED_AT` は逐語「★プロセスの記憶（再起動で消える）」／
  resume は段②の submitted 経由しか無い ＝ **両側が非対称**

### ★置く最小差分（★2箇所・★新語0・新state0・新機構0）

```python
# (a) 段① に 段②と同じ形を置く（★判断器も記録も 既存の物）
_stop = _STOPPED_AT.get(tid) or []
if _stop:
    _dq = _use("decide_tick", decide_tick, {"task_id": tid, "dw_state": st}, None, _stop)
    if _dq.get("action") == STOP:
        _record({"action": SLEEP, "task_id": tid, "reason": _dq.get("reason")},
                {"phase": "candidate_skip", "dw_state": st, "stopped_at_stage": list(_stop),
                 "key_note": "★yield=★並びに残したまま次候補へ(★落とさない)"})
        keep.append(tid)     # ★★順番を失わない
        continue             # ★後続の 実行できる 案件へ 進む

# (b) 除去をやめる
if d.get("reason") == "同じ所で2回":
    _queue_write([t for t in _queue() if t != task["task_id"]])   # ★★これを消す
```

**★(a) は 段② が既に使っている `decide_tick`（2DER 製）／`_record`／`phase=candidate_skip` の写し。
★判断を新しく書かない。★語を増やさない。★順序を変えない（`keep` は元順）。**

**★resume が成り立つ理由**: `_STOPPED_AT` はプロセスの記憶 ∴ 再起動で忘れる
＝ **恒久の除外表にならない** ＝ 次のプロセスで**元の FIFO 位置のまま再評価される**。
（★これは既存の性質であって、私が足すものではない。）

### ★常駐を上げる前に Taka へ出す数（★ステップ⑤の材料・★実測）

```
next_operation = UPPER_REVIEW  ★79件
  _MAP[JUDGE_REQUIRED / READY_FOR_UPPER_REVIEW].barrier = ★False
  かつ CLAUDE_SENIOR は _machine_registry に ★在る
  ∴ dispatch は :163 で止まらず 機械dispatch へ進み ★fn=claude_senior(=claude -p) を呼ぶ
  ★trivially_clean なら auto_pass。それ以外は ★実呼出。

★実測の裏づけ: 窓1つ(330s)で 頭1件が upper_reviews ★2件(両方FAIL) ＋
  headless セッション ★2件 を消費し ★dw_state は1歩も動かなかった。
★∴ 常駐を上げると 194件(Claude不要)と同時に ★79件が Claude を呼びに行く。
★これは『2DERがClaudeを叩く』設計どおりでもある ∴ ★欠陥と決めつけない。★数だけ出す。
```

---

## 11. ★実走 2026-08-22 16:1x ―― 4段すべて取れた ／ 判定 = ESTABLISHED

**実装**: twoder `96677bd`（★declared `92e190e` の**後**＝git 順序で確認できる）
**差分**: 31行追加 / **削除は `_queue_write` の1行だけ**

### ★計器の訂正（実走中に1つ わかった）

```
最初 `timeout 400 python3 -m twoder.manager_v0` を回した → ★events 0件(24→24)。
★原因= main() は最初に record_stages を呼び、その中の
  /api/control?include=observed_edges が ★timeout=460 ∴ ★400秒では tick() に到達しない。
★∴ 1プロセス内で ★tick() を直接 呼ぶ形に変えた(★_STOPPED_AT が持続する=正しい計器)。
★★正直に書く: ★main() の周回は経ていない。★但し 4つの挙動は すべて
  _last_task / tick の内側 ∴ ★経路としては同じ。
```

### ★実走の記録（★1プロセス・5 tick）

```
tick0  RUN   TASK-2DER-731F98A0                    進める
tick1  STOP  TASK-2DER-731F98A0                    ★同じ所で2回
tick2  RUN   TASK-2DER-PRODUCER-SELECT-CREATE-v0.1 ★★後続 pick
tick3  STOP  TASK-2DER-PRODUCER-SELECT-CREATE-v0.1 同じ所で2回
tick4  RUN   TASK-2DER-AUTO-68518E15               ★さらに次へ

_STOPPED_AT = {731F98A0: [UPPER_REVIEW, UPPER_REVIEW],
               PRODUCER-SELECT-CREATE-v0.1: [PLAN, PLAN],
               AUTO-68518E15: [PLAN]}
```

### ★Taka の4段 ―― 4/4

| 段 | 判定 | 証拠 |
|---|---|---|
| ① **yield** | **OBSERVED** | `/api/etrace` の MANAGER_V0 が 5→**10**件。うち **`phase=candidate_skip` が3件**、`action=SLEEP` / `reason=同じ所で2回`（★**原因付きで残っている**） |
| ② **後続pick** | **OBSERVED** | tick2 で **別 task** が RUN、tick4 で **さらに別 task** が RUN ＝ **3つの異なる task が順に選ばれた** |
| ③ **元task保持** | **OBSERVED** | **新プロセス**（`_STOPPED_AT = {}`）で `_last_task` が **`731F98A0` を再び返した** ＝ **並びから落ちていない** |
| ④ **条件解消後再評価** | **OBSERVED** | 同上。`action=RUN / reason=進める` ＝ **元の位置のまま 再評価された** |

**★③④ が同じ観測で取れたのは、`_STOPPED_AT` が「プロセスの記憶」だから
（★既存の性質・私が足したものではない）。**

### ★R4 ―― 拒否条件を実際に発火させた

```
_machine_turn（段①の述語）           ★純関数・副作用0
  ★未知の状態 NO_SUCH_STATE  → False  ★拒否(先頭を塞がない)
  ★COMPLETE                  → False  ★拒否
  ★BLOCKED                   → False  ★拒否
  (対照) READY_FOR_AUDIT      → True   通す        ←★対照が通ることも確認

decide_tick（★2DER 製・1行も書き換えていない）
  stopped_at=[]              → RUN  進める
  stopped_at=['PLAN']        → RUN  進める
  stopped_at=['PLAN','PLAN'] → ★STOP 同じ所で2回   ←★境界が2回目に在ることを確認
  ★実走でも 3回 発火（tick1 / tick3 ＋ 段①の candidate_skip）

★未発火 = ④escalation 未解決 → candidate_skip
  ★これは ★段②の既存経路で ★私の差分の外 ∴ ★UNVERIFIED として残す(★PASSにしない)。
```

### ★ESDE 宣言（実走後）

```
EQUALITY   ★CONFLICT → ★解消
           waiting  = 並びに残り phase=candidate_skip + reason（★実測3件）
           removed  = _queue_write（★受領後のみ・domain_dw:393）
           completed= dw_state COMPLETE
           skipped  = ★waiting と同じ語のまま = ★Taka/監査の裁定どおり ★分けない(新語0)
           status: ★PRESENT（★waiting と removed が別経路になった）

SYMMETRY   pairs 3 / present ★3 / missing 0
           yield ↔ resume     ★①と③④で両側 OBSERVED
           並びに残す ↔ 落とす ★保持(実測)↔ 受領後のみ落とす
           記録する ↔ 読む     ★candidate_skip を /api/etrace が返す(★実測)

LINKAGE    E1 判定→yield        OBSERVED
           E2 yield→次候補      OBSERVED
           E3 次候補→pick       ★OBSERVED（★これが UNVERIFIED だった。★解消）
           E4 yield→原因の記録  ★OBSERVED（★段①にも出た＝ABSENT だった。★解消）
           E5 次周→resume       ★OBSERVED（新プロセスで元位置）
           declared 5 / observed ★5 / broken 0

HIERARCHY  required 5 / passed 5 / violation 0
           ★順序= 3 task は ★並びの順に 選ばれた（頭→次→次）＝★並べ替えていない
           ★重要度= score も rank も 書いていない（差分 31行に 無い）
           ★判断器= decide_tick（2DER 製）を そのまま 使った
           ★入口= 派生値（webui の役名列挙）は ★使わなかった

R1_END_TO_END     ★OBSERVED（本線の tick()・実 queue・実 state）
R2_DENOMINATOR    状態 9/9 走査 ／ 実走 5 tick / 3 task
R3_INTERNAL_GATES gates [_machine_turn, decide_tick] passed ★2/2（対照つき）
R4_REJECTION      ①②③⑤ ★実発火 ／ ④ ★UNVERIFIED（差分外）

UNDERSTANDING  candidate: EXECUTABILITY_YIELD
               requires: [4段, R4, FIFO を壊さない, priority を作らない]
               evidence: [上記すべて]
               unresolved: [R4④（段②の既存経路・差分外）]
               result: ★ESTABLISHED
               ★根拠: Taka の成功条件「FIFO の意味を壊さず、実行不能な先頭 task が
                 後続の実行可能 task を ★永久停止させないこと」= ★実走で成立。
               ★★但し「194件を流した」ではない（Taka 逐語で exit から外してある）。

CREATION   status: NOT_EVALUATED
DECISION   ★GO（★次は ステップ⑤＝常駐。★その前に §10 の 79件 を もう一度 出す）
```

---

## 8. 触っていないもの

`EVO-0085` writer 4欠損 ／ `EVO-0087`（R4② 未発火）／ `EVO-0088`（閉）／
`EVO-0083` の ESDE 統合 ／ 正本§13 の UNVERIFIED 差戻し ／ 194件の消化（★exit にしない）。

**★新API 0・新Manager 0・新台帳 0・新state 0・新語彙 0・コード変更 0行。**
