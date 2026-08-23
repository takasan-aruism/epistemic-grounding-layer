# required source resolver — 設計 v0.1（★設計のみ・実装しない）

**発: 監視（3Claude の外部・CC_ALPHA） ／ 宛: Taka ・ MGR ／ ✔ は付けていません**
**★コードは1行も変えていない。★新しい Manager / Worker / 台帳 / ID / 経路 / state を1つも作っていない。**
測ったHEAD: twoder `405a423` / rri `da04d89` / egl `780c47e`
根拠: **Taka 裁定 2026-08-23（required の独立出所4源）／ 2026-08-24（明細を③として正式採用・唯一の供給源にしない）**

---

## 0. この設計が答えること

ESDE の階層性は `required − enforced = violation` で測る（裁定済み）。
**残っていた唯一の穴は「独立した required をどこから供給するか」**であり、本書はその1点だけを設計する。
**★測定器は1つも増やさない。★実装して大量適用しない。**

---

## 1. required の供給源（★4源を並列。順位は付けない）

```
① TAKA_RULING        Taka 裁定
② CANONICAL_DOC      正本文書
③ DESIGN_DETAIL      確定済み設計明細 ―― ★kind が SPEC / CONSTRAINT / GOAL のもの
④ PLAN_CONTRACT      確定済み PLAN / contract
```

**★「明細が無いから required も無い」にはしない**（Taka 逐語）。
③が空でも ①②④ から供給できる。**③は追加の面であって、置き換えではない。**

**★enforcement と同じコード上の定数や門は required の正本にしない**（Taka 裁定 2026-08-23）。
∴ `_ALLOWED`(dw) / `TRANSITIONS`(rri) / `authority.POLICY` / allowlist定数 の**92件は候補のまま**であり、
required 側には置かない。

---

## 2. 出力の形（★7欄）

```
required_id      この required 1件の識別子
statement        あるべき事の 本文（★原文のまま。要約しない）
source_kind      TAKA_RULING / CANONICAL_DOC / DESIGN_DETAIL / PLAN_CONTRACT
source_id        出所の 既存ID（例 Q-… / QT-… / DE-… / TASK-…）
version          出所の 版（★③なら typed_id の 現在有効版）
axis             どの AXIS の required か
status           REQUIRED / SUPERSEDED / WITHDRAWN
```

**★なぜ由来を残すか（Taka 逐語）:「なぜこれを required と数えたのか？」まで追えるようにするため。**
∴ `source_kind` と `source_id` は**必須**。空にしない。

**★新しい ID 体系を作らない。** `required_id` は既存の出所IDから導出する
（③なら `typed_id` そのものを使えば足りる）。**新しい接頭辞を増やさない**
――今日の実測で、発行30種のうち22種が相互参照の口から引けないことが分かっている。

---

## 3. ③（明細）から読む時の規則 ―― ★履歴を required に数えない

**Taka 逐語:「ESDE側が required を読むときは、132履歴行を全部 required として数えてはいけません。
読むべきなのは原則、各 typed_id の現在有効版です。」**

```
履歴 132行
   ↓ projection（★`rri.request_thread.list_typed` が既に行っている
                 ―― 逐語「同じ typed_id が2度在れば 後の行が効く」）
現在有効 33明細
   ↓ kind で 絞る
SPEC / CONSTRAINT / GOAL のみ = ★14件
   ↓
required candidates
```

**★読み口は既に在る。新しく作らない。** `list_typed(thread_id)` が projection 済みの33を返す。
**★これは版管理が既に実質的に働いている例である**（Taka 指摘）。

---

## 4. 現時点の母数（★実測・2026-08-24）

```
構造化明細を持つ thread   ★1 / 647（0.2%）
その thread の 現在有効な明細   33件（追記の履歴は 132行）
★うち あるべき側(SPEC/CONSTRAINT/GOAL)   ★14件
```

**∴ ③は型としては正しいが、現時点では母数が足りない**（Taka 判断と一致）。
**★「明細が育つのを待つ設計にしない」（v0.2 §4）はそのまま生きる。**
初期の ESDE は ①②④ を主とし、③は**在る依頼で精度を上げる面**として使う。

---

## 5. 三面照合 1回の実測（★AXIS=ED65242E ／ 裁定どおり1回だけ通した）

**required 14件（すべて `source_kind=DESIGN_DETAIL`）に対し:**

| | 件数 |
|---|---|
| enforced ○ | **2** |
| enforced × | **8** |
| enforced ?（UNVERIFIED） | **4** |
| observed ○ | **0**（14件すべて未到達） |
| **required − enforced = 構造欠損** | **★8件** |

**★enforced ○ の2件**
```
CONSTRAINT 日本語10〜15文字・体言止めは現行のまま        → account_gate の段2に在る
CONSTRAINT 既存の承認経路(/api/approve)は現行のまま使う  → 口が在る
```

**★enforced × の8件（すべて同じ原因）**
```
SPEC 関数名は classify_account。引数は2つ(vote, existing_accounts)
     ＋ その署名・返り欄・status の3値・3分岐・設定読み込みの位置
★原因= `classify_account` が存在しない ∴ 署名も返りも分岐も enforce されようがない
```
**★名前だけで判定していない。** 今日5回の計器訂正の教訓に従い**作用でも探した**:
`(vote, existing_accounts)` を取る関数 = **0件** ／ `in_pending` を持つコード = **0件** ／
`INVALID_BOOK_NAME` = **試験ファイルにのみ存在**。**∴ 別名で実装されてもいない。**

**★enforced ? の4件（★推測で埋めない）**
```
CONSTRAINT 新しい API の口・台帳・state・語を増やさない
   → ★数える計器は在る（front door の口 22 / 登記された台帳 56冊）が ★比較する前の値が無い
CONSTRAINT 既存の574件は現行のまま残す ／ GOAL 574件が574件のまま在ること
   → ★574 が どの台帳の 何の件数か 明細に書かれていない = ★分母の鍵が不明
GOAL 封印試験6件が全て通ること
   → この task の 試験実行の記録を 引けていない
```

**★observed が 0 なのは 計器の欠陥ではない** ―― enforce されていないので**実走で確かめる対象が無い**。
この task は実装前である。**「まだ作られていない」を機械が見えた**、が正しい読み方。

---

## 6. ★この一周で分かった、明細を required にする時の実務的な要件

実測から**3つ**出た。いずれも**新しい欄を作らずに済む**。

```
①『現行のまま』は 比較する前の値を 明細が持たないと 判定できない
   → 4件中2件が この理由で UNVERIFIED になった
②『574件』のような数は ★何の件数か（鍵）を 併記しないと 数えられない
   → 私が本日3回 自分の数字を訂正した原因と 同じ型
③ SPEC は 実装の識別子（関数名）を名指しする ∴ ★その識別子が 引けることが前提になる
   → 発行30種のうち22種が引けない現状と 直結する
```

---

## 7. ここで止める（★Taka 裁定 2026-08-24）

**逐語:「まだ実装して大量適用する必要はありません。まず ED65242E の14件程度で
明細required → enforced → observed の三面照合を1回だけ通せば十分です。」**

```
★通した = 本書 §5
★止める = resolver の実装 ／ ①②④からの供給 ／ 他 AXIS への適用 ／ 測定器の追加
```

---

## 8. していないこと

```
★実装 0行 ／ 新しい Manager / Worker / 台帳 / ID / 経路 / state 0
★測定器の追加 0 ／ blocking 0 ／ 他 AXIS への適用 0
★既存仕様の書き換え 0 ／ ED65242E の実装への関与 0（★構造欠損8件は 報告のみ・私は直さない）
★required 4源のうち ①②④ からの供給は ★設計に書いただけで 実測していない
```
