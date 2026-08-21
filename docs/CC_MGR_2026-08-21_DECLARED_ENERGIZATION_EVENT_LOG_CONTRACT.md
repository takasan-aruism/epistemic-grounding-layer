# declared — AXIS = `ENERGIZATION_ADJUDICATION_WRITER`（継続・接続先の契約を確定して立て直す）

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
開発者規律 確認済(`2DER_DEVELOPER_DISCIPLINE_v1.0` / `TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3`)
**★実装の前に置く1枚。★コードは1行も変えていない。**
測ったHEAD: twoder `065325e` / dev-workcell `68c3b4c` / egl `d48152e`

**★これは Taka 指摘「ESDE の理論の上に自分の行動を定めろ。最短ルートが最善とは限らん」への立て直し。**
前回の私は ①AXIS宣言・③因果鎖・⑤declared を飛ばし、②全件調査を**依頼先の制約だけ**に限定した。
その結果 **安全弁を緩める方向の仕様**（ts 昇順ソート）で部品を作らせた。**repo には入れていない。**

---

## ① AXIS 宣言（境界を先に固定する）

```
対象      Taka の承認1件が 既存 minter に読まれるまでの経路
入口      POST /api/approve（既存2枝のうち ★枝2 = issue_approval）
出口      bridge_minter.mint_real_energize が token を発行する
authority 発行 0・変更 0。既存 authority(may_approve / grant_approval)をそのまま使う
保存先    既存2台帳のみ。★新しい保存先 0
          egl/ENERGIZATION_LEDGER.jsonl ／ egl/ENERGIZATION_OBSERVATIONS.jsonl
下位構成  (a) identity rule の1語追加  (b) 承認の writer  (c) 2台帳を併合する reader
範囲外    apply_cycle 以降 ／ 並行運用(EVO-0084) ／ 周辺欠陥
```

## ② 全件調査 ―― ★接続先の契約（前回ここを飛ばした）

**探索範囲** = `ds rri egl dev-workcell twoder` の `*.py` 全件。

### ★確定1: 順序の正本は **append 位置**。`ts` は順序の鍵ではない。

| 根拠 | 実測 |
|---|---|
| 消費側が位置で読む | `bridge_reconciler.py:245` `for i, e in enumerate(event_log)` ／ `:265` `:271` `event_log[last_recon_idx+1:]` |
| 消費側は `ts` を読まない | `bridge_minter.py` の `ts` 出現 **0**。`bridge_reconciler.py` の `ts` は2箇所とも `emit_reconciliation` の引数を recorder へ渡すだけ |
| `ts` は実データで逆行する | **append 順に対し ts 逆行 843 / 4275 ＝ 19.7%**（監査が全件で計測）。例 `idx25` 09:00:00→08:00:00 ／ `idx39` 07-13T01:16→07-11T08:00 |
| 競合する消費者は本線に居ない | `ts` 順に並べる箇所は `twoder/submit.py:149` の**1件のみ**（roadmap の failure を新しい順に1件選ぶ用途・reconciler と交わらない） |

**∴ 対等性は CONFLICT ではない。** 権威は1つ（append 位置）で、**私の仕様が誤っていただけ**。

### ★確定2: 順序に依存する検査は **1件だけ**。

| 検査 | 順序依存 | 根拠 |
|---|---|---|
| `_find_adjudication` | **無** | `adjudication_id` で探す（`bridge_minter.py:48-52`） |
| `_is_revoked` | **無** | `adjudication_id` で探す（`:55-60`） |
| `_token_id_consumed` | **無** | `token_id` で探す（`:62-68`） |
| (3a) unbound `PATCH_APPLICATION` | **無** | 全走査（`:118-123`） |
| (3c) `bound_here` 抽出 | **無** | 全走査（`:140-`） |
| **(3b) `latest_balance_proof`** | **★有** | 最後の `RECONCILIATION_*` の index → その後の `PATCH_APPLICATION` の有無（`bridge_reconciler.py:243-275`） |

**(3b) が読む3つの kind** ＝ `RECONCILIATION_BALANCED` / `RECONCILIATION_IMBALANCED`（`bridge_reconciler.py:31,33`）/ `PATCH_APPLICATION`。
**3つとも bridge・reconciler の観測** ＝ `egl/ENERGIZATION_OBSERVATIONS.jsonl` 側（DE-0438 decision 逐語
「event store: `egl/ENERGIZATION_LEDGER.jsonl`(Taka 書込 judo1/2) + `egl/ENERGIZATION_OBSERVATIONS.jsonl`(bridge/reconciler 観測)」）。

**∴ 順序に依存する唯一の検査が読む kind は、すべて同じ1ファイルの中にある。
∴ ファイル間の交錯順序は、どの検査にも影響しない。**

### ★確定3: ∴ 正しい併合は **単純な連結**。ソートしない。

```
merged = ledger_rows + observation_rows      # 各ファイルの内部 append 順をそのまま保つ
```
`ledger_rows` を先に置く理由：後ろに置くと `last_recon_idx` 以降のスライスに承認行が混ざる
（`PATCH_APPLICATION` ではないので無害だが、**観測の尾部だけがスライスに入る形**の方が意図が明確）。

**★前回作らせた「ts 昇順ソート」は不要どころか有害だった。** repo には入れていない。

### 残る UNVERIFIED

```
LEDGER_ROW_FIELD_NAMES_NOT_READABLE
  各行が実際に kind / payload の鍵をその名前で持つかは front door から読めない。
  台帳の直読は禁止（本日6回・累計53回 拒否された）。読み出す口が無い。
  ★但し 順序については 消費側の実装から確定できた ∴ この AXIS では止める理由にならない。
```

## ③ 因果鎖

```
① Taka が押す      →(Basic 認証)→ APPROVED_BY = "taka-credential"（webui.py:97）
② 人か判定         may_approve（command_surface.py:38）が INTERIM_APPROVERS で ★既に通す
③ principal 判定   principal_of（principal_attribution.py:22）が ★UNKNOWN_PRINCIPAL を返す ← ★欠損(a)
④ 承認を記録       egl/ENERGIZATION_LEDGER.jsonl へ ENERGIZATION_ADJUDICATION ← ★欠損(b) 書き手0
⑤ event_log を作る 2台帳を連結 ← ★欠損(c) 読み手0
⑥ token 鋳造       mint_real_energize（bridge_minter.py:71）★実在・DE-0438 で完走実績
⑦ 以降            apply_cycle → rollback → reconciler → single-use ★DE-0438 で完走実績
```

**止まっている点は ③④⑤ の3つだけ。⑥⑦ は 2026-07-19 に完走している（DE-0438）。**

## ④ DESIGN_HOLD 判定

**推測が残る点＝1（`LEDGER_ROW_FIELD_NAMES_NOT_READABLE`）。** ただしこれは
**順序の決定には関与しない**（確定1・2で消費側の実装から確定済み）。
∴ **DECISION = GO**。ただし **(c) reader の実装時に、行の鍵名を仮定した箇所を UNVERIFIED として明示する**こと。

## ⑤ ESDE 宣言

```
EQUALITY   canonical = append 位置。producer=各台帳の追記。consumer=bridge_minter / bridge_reconciler。
           ★identity rule = リスト内の位置。★ts は identity ではない。
           status = ★PRESENT（CONFLICT ではない。競合消費者0を全件 grep で確認）
SYMMETRY   required 3 = (a)identity rule (b)writer (c)reader
           present 0 / missing 3。missing_ID = TAKA_CREDENTIAL_HAS_NO_PRINCIPAL_RULE /
           ENERGIZATION_ADJUDICATION_HAS_NO_WRITER / ENERGIZATION_EVENT_LOG_HAS_NO_READER
LINKAGE    declared 7（①〜⑦）/ observed 2（⑥⑦＝DE-0438）/ broken 3（③④⑤）/ unverified 2（①②は本経路で未実走）
HIERARCHY  required 3 (1)判断は 2DER 製の純関数が持つ (2)既存 authority を変えない
           (3)writer は承認記録まで・token は minter・適用と commit は apply_cycle
           passed 3 / violation 0
UNDERSTANDING  候補 = TAKA_APPROVAL_REACHES_MINTER。★まだ ESTABLISHED にしない。
               要件 = ③④⑤ が塞がり ⑥が正規上流から1回通ること。
CREATION       NOT_EVALUATED
DECISION       GO（実装は次段。この declared は実装の前に commit する）
```

## ⑥ 進捗の数え方（Taka 逐語）

**「PLAN が少し良くなった」も「速く1周 COMPLETE した」も進捗に数えない。**
進捗の起点＝**Taka 承認 → /api/approve → ENERGIZATION_ADJUDICATION → merged event_log → bridge_minter が正規経路で1回通った時点**。

## ⑦ 触っていないもの

`merge_records`（UNVERIFIED・repo 未配置・構成要素に使わない）／並行運用 EVO-0084 ／
apply_cycle 以降 ／ 周辺欠陥 ／ 未commit 30件 ／ 台帳 mismatch ／ D188・D190。
