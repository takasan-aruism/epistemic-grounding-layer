# 宛: Taka ―― **既存欄だけで どこまで 表せるか（★4問・★実物・★実装 0）**

**2026-08-20 03:1x ／ ★新しい 欄 0 ／ 語 0 ／ 台帳 0 ／ 関数 0 ／ ★結論を 先に 決めていない**

---

## 問1 ★ITEM を「上位の 問題・能力・目的の 単位」と して 扱えるか → **★扱える**

```
★`ITEM-2DER-EVO-0019` の 実物:
   kind     = ★"ITEM"
   title    = "Independent audit layer (independence conditions defined; …)"
   status   = ★"IN_PROGRESS"
   phase_id = "PHASE-2DER-EVO-08"
   ★acceptance = ★在る（★受入条件の 本文・★「CHECKLIST DISCHARGE … SKELETON FIXED: [i] … [ii] …」）
   ★status_note = ★在る（★最新 = 「actor=MGR stage=PLAN via=front_door run=ETR-… note=…」）
★★＝ ★『目的（title）』『受入条件（acceptance）』『状態（status）』『段（phase_id）』が ★既に 揃っている。
```

## 問2 ★複数 TASK を 同一 ITEM の 下位作業と して 束ねられるか → **★既に 束ねている**

```
★`ITEM.task_ids` = ★37件
★★今夜の 実例 5件 ―― ★すべて ∈ ITEM:
   E8AAEA8C ★True ／ 070D062A ★True ／ CBAFD9EC ★True ／ 3361D3E1 ★True ／ A36B3881 ★True
★★＝ ★束ねる 器は ★既に 在り ★実際に 使われている。
```

**★但し 粒度（★事実）:**

```
★★37件が ★1つの ITEM に 平らに 並ぶ。
★★∴ ★『E8AAEA8C の 停止』と『070D062A は その 修理』は ★兄弟に なる ―― ★親子に ならない。
★★∴ ★ITEM だけでは ★どれが どれの 修理かは ★区別できない。
```

## 問3 ★子 TASK の 成果で ITEM の 停止理由が 解消したことを 既存欄で どこまで 表せるか

**★実測（★履歴 ★全121件 を 走査）:**

| 見た もの | 結果 |
|---|---|
| `status_note` に task id が 出た 回数 | `E8AAEA8C` ★4回 ／ ★`070D062A` `CBAFD9EC` `3361D3E1` `A36B3881` は ★★0回 |
| `stage` の 内訳 | PLAN 55 ／ DETECT 22 ／ RECORD 12 ／ ADJUDICATE 11 ／ IMPLEMENT 8 ／ VERIFY 6 ／ RECEIVE 3 |
| 解消を 表す 語の 出現 | 「解消」2 ／「解決」2 ／`resolved` 2 ／`closed` 11 ／`satisfied` ★0 ／「還流」4 |
| 履歴 1件の 欄 | ★ITEM の 全欄の ★スナップショット（16欄）＝ ★task 単位の 欄は ★無い |

```
★★＝ 表せる のは ★★『ITEM 全体の 状態が いつ どう 変わったか』まで。
★★＝ 表せない のは ★★『どの 子 TASK の 成果が ★どの 停止理由を 満たしたか』。
★理由（★構造）:
   ・履歴は ★ITEM の 丸ごとの 写し ∴ ★粒度が ITEM
   ・`status_note` は ★自由文 ∴ ★書けば 残る が ★★機械が 引ける 欄では ない
     （★実測: ★私が 書いた 4回だけ task id が 入っている ／ ★機械は 1回も 入れていない）
   ・`acceptance` は ★ITEM 全体の 受入条件 1本 ∴ ★停止理由の 個別には 割れていない
```

## 問4 ★階層を ITEM 階層・依存から 導出できるか

**★既に 在る 階層（★実物・4段）:**

```
★ROADMAP-2DER-EVOLUTION-v0.1（kind=ROADMAP ／ title="2DER Evolution Roadmap"）
   └ ★PHASE-2DER-EVO-08（kind=PHASE ／ title="Supervised autonomy & operating economy" ／ ★order 欄あり）
      └ ★ITEM-2DER-EVO-0019（kind=ITEM ／ ★depends_on=[EVO-0016, EVO-0017] ／ ★task_ids 37件）
         └ ★TASK-2DER-…（★37件）
```

```
★★＝ ★『組織の 階層』は ★ROADMAP / PHASE / ITEM / TASK の ★4段で ★既に 在る。
★★但し ―― ★ご指示の 階層は ★TASK / COMPONENT / PIPELINE / SYSTEM
   ＝ ★★『問題が どの 層に 属するか』であって ★『作業の 入れ子』では ない。
★★実測: ★`COMPONENT` `PIPELINE` `SYSTEM` に 相当する 語は
   ★ROADMAP/PHASE/ITEM の どの 欄にも ★出ない（★kind は ROADMAP/PHASE/ITEM の 3語だけ）。
★★∴ ★組織の 階層は 導出できる が ★『問題の 層』は ★導出できない。
   （★対応づける なら ★人が 決める 必要が ある ―― ★私は 決めていない）
```

## ★『TASK を 直接 結ぶ 必要が 本当に あるか』（★結論を 決めない・★材料だけ）

**★直接 結ばなくても 済む かもしれない 材料:**

```
★① ITEM は ★既に 束ねている（★37件・★実例 5件 とも 入る）
★② ITEM には ★acceptance（受入条件）と ★status_note（自由文）が ★既に 在る
★③ ITEM 間の 依存は ★`depends_on` で ★既に 表せている（★実データ 2件）
★④ ★`provenance.dw_task_id` が ★各 task に 在る ∴ ★ITEM → TASK は 双方向に 引ける
```

**★直接 結ばないと 足りない かもしれない 材料:**

```
★⑤ 37件が ★平ら ∴ ★『修理 ↔ 被修理』が ★兄弟に なる（★区別が 付かない）
★⑥ ★acceptance は ★ITEM に 1本 ∴ ★停止理由が 複数 あると ★どれが 満ちたか 割れない
★⑦ ★履歴は ★ITEM 丸ごとの 写し ∴ ★task 単位の 解消を ★機械が 読めない
★⑧ ★実測: ★機械が status_note に task id を 入れた 回数 = ★★0
   （★4回は ★すべて 私が 手で 書いた もの）
```

```
★★∴ ★『ITEM を 細かく 割る』でも ★『TASK を 直接 結ぶ』でも ★どちらでも 表せる 可能性が ある。
★★私は ★どちらが 良いかを ★決めていません（★ご指示どおり）。
```

## ★していないこと

```
★新しい 欄 0 ／ 語 0 ／ 台帳 0 ／ 関数 0 ／ 配線 0 ／ ESDE 未実装
★4不足（parent 欄 / affects / 階層語彙 / 子の成果で解消の語）は ★実装していない
★実 repo 書き込み 0 ／ 常駐 停止のまま ／ DISPOSE 0（★滞留 2件は 未接触）
★SELF_DEV_TOKEN = ★5/5
★★推測で 埋めた 欄 0 ―― ★『無い』は ★走査した 範囲を 明記した もの だけ
```
