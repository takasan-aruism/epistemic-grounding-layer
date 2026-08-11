開発者規律 確認済(v1.0)

# 【BUILD SPEC】★権限の規則（★3層）を ★機械の値だけで 決める

宛: IMPL ／ 発: DESIGN ／ 2026-08-11 16:20 ／ 台帳: `ITEM-2DER-EVO-0062`
出所: **Taka 逐語**（3層・`risk_class / evidence / rollback / authority / decision`）＋ MGR 条件（★risk_class は決定論／★evidence と rollback は機械が導く／★層2の条件を我々が増やせない／★層3は常に Taka／★材料が無い物は層3＝fail-closed／★層1で通った件を Taka が後から一覧で見られる）

---

## 1. ★材料の実測（★母数つき・★2026-08-11 16:00）

```
★★risk_class の材料 = ★`twoder/authority.py` の ★POLICY ★22行
   ★段の分布 = ★★OBSERVE 9 ／ ★REVERSIBLE 3 ／ ★IRREVERSIBLE 10
★★evidence の材料 = ★`trace_status`（★`ETR` が 実在するか）= ★★OK 27 ／ UNVERIFIED 154（★母数181）
★★rollback の材料 = ★`revert_scope.complete` = ★★75/181
★★影響の広さ = ★`affected_artifact_ids` の件数 = ★★1件 75 ／ ★2件以上 103 ／ ★0件 3（★母数181）
```

## 2. ★★私が 見つけた 落とし穴（★★先に 書く・★★これを 避けないと 憲法が 全閉めになる）

```
★★『evidence は ★その item の 過去の CHG に OK が 在ること』と 書くと ―― ★★破綻する。
★★実測: ★CHG を持つ item(de_id) = ★131件 ／
        ★★そのうち ★evidence=OK が 1件以上 在る item = ★★★1件（★131件中）。
★★∴ ★★層1 は ★★ほぼ 空 → ★★★全部 層3 = ★★★今夜の『全部 閉め切った』の 再来。

★★∴ ★★★evidence は ★★『★いま その行為が 通ってきた 1本』で 判定する。
   ―― ★行為は ★front door を 通って 来る ∴ ★★その run の `trace_id` は ★★実在の ETR
   ―― ★★過去の履歴を 条件に しない（★過去は ★参考として 併記するだけ）
★★[[absence-reads-as-compliance]]: ★★『記録が 無い』を ★『満たした』にも『違反』にも しない。
```

## 3. ★★決定表（★★決定論のみ・★★LLM 0回・★★人の文を 1つも 読まない）

```
★★risk_class ← ★段（★POLICY の3値）と ★影響の広さ
   ★段 OBSERVE                → ★★`OBSERVE`
   ★段 REVERSIBLE + 影響が 狭い → ★★`REVERSIBLE_LOCAL`
   ★段 REVERSIBLE + 影響が 広い → ★★`REVERSIBLE_WIDE`
   ★段 IRREVERSIBLE            → ★★`IRREVERSIBLE`
   ★表に 無い行為 / 段が 読めない → ★★`NOT_DECIDED`

★★evidence ← ★★その行為の `trace_id` が ★実在の ETR（★`trace_status == "OK"`）
★★rollback ← ★★`revert_scope(...).complete`
             ★★但し ★段 OBSERVE は ★★`NOT_REQUIRED`（★★書かない行為に 戻す物は 無い）

★★decision（★★これが 台帳に 残る主役）
   ★★層1 `AUTO_APPROVED`             ← ★`OBSERVE`
                                      ★または（`REVERSIBLE_LOCAL` かつ evidence=OK かつ rollback=complete）
   ★★層2 `AUTO_APPROVED_CONDITIONAL` ← ★`REVERSIBLE_WIDE` かつ evidence=OK かつ rollback=complete
   ★★層3 `REQUIRES_TAKA`             ← ★`IRREVERSIBLE` ／ ★`NOT_DECIDED`
                                      ／ ★evidence≠OK ／ ★rollback≠complete（★fail-closed）

★★★固定条項（★1文字も 緩めない）
   ★`CHANGE_AUTHORITY_CEILING` と ★権限境界そのものの変更 = ★★★常に 層3
   ―― ★★段が 何であっても 覆らない（★★自己昇格の 錠）
```

## 4. ★★裁定を 求める 1点（★★我々が 決めてはいけない所）

```
★★『影響範囲は 広い』の ★★機械の定義が ★★Taka の規則に 書かれていない。
★★MGR 条件『層2の条件を 我々が 増やせない』に 直接 当たる ∴ ★★★我々は 決めない。

★★案A: ★`affected_artifact_ids` が ★2件以上 = 広い
        → ★★実測 ★広い 103 ／ 狭い 75（★母数181）
★★案B: ★成果物が ★2つ以上の repo に またがる = 広い
        → ★★未測定（★★測るには artifact_registry を 引く=★★数を 出してから 決めてよい）

★★どちらでもない案（★★Taka が 別の言い方をする）も 在り得る ∴ ★★★聞く。
★★★決まるまでの 扱い = ★★`REVERSIBLE_WIDE` は ★★出さない = ★★層2 は 0件
   → ★★『層2 は まだ 動いていない』と ★正直に 書く（★★『在る』と 書かない）
```

## 5. ★★記録の形（★★保存0増・★口0増・★新台帳0）

```
★★導出して 載せる（★★本日 確立した形を そのまま 使う）
   ★`GET /api/resolve?id=…` の 応答に ★★`authority_decision` を 足す
      = ★`{risk_class, evidence, rollback, authority, decision, rule}`
   ★★`rule` = ★★どの規則で 通ったか（★Taka 逐語『どの規則に基づいて、どの権限レベルで通ったか』）
      ―― ★例: `"OBSERVE ∴ 層1"` ／ `"IRREVERSIBLE ∴ 層3"` ／ `"rollback≠complete ∴ 層3(fail-closed)"`

★★層1で 通った件の 一覧（★★Taka が 後から 見る・★MGR 条件）
   ★既存の ★`GET /api/control` の 応答に ★★`authority_summary` を 足す
      = ★★層ごとの 件数 ＋ ★★★ids（★★数だけ 出さない=★名前で 並べる）
★★∴ ★★口 0増 ／ ★保存 0増 ／ ★新台帳 0
★★部品と 呼び手は ★★同じ変更で 入れる（★★本日 規律に なった条件）
```

## 6. ★★受入（★数で・★★走らせる前に 宣言する）

```
★★【★直す前の値】★★層という語で 通った行為 = ★★★0件（★★規則が まだ 無い）

★① ★`GET /api/resolve?id=CHG-…` に ★`authority_decision` が 在る（★★181/181）
★② ★★`decision` が ★3つの語だけ（★`AUTO_APPROVED` / `AUTO_APPROVED_CONDITIONAL` / `REQUIRES_TAKA`）
★★③ ★★層1 の件数が ★★★0 で ない（★★『全部 閉め切る』の 再発検知＝★MGR 条件）
★★④ ★層2 = ★★0件（★§4 が 決まるまでは ★0が 正しい・★★0件と 書く）
★★⑤ ★`CHANGE_AUTHORITY_CEILING` を ★どの段で 試しても ★★層3 に 落ちる（★1件 実物）
★★⑥ ★★`rule` が ★全件に 在る（★★★『どの規則で 通ったか』が 空の行 = 0件）
★★⑦ ★★LLM の呼び出し = ★★★0回（★機械で 数える）／ ★人が 書いた文を 読む所 = ★★0箇所
★★⑧ ★`GET /api/control` から ★層ごとの ★★件数と ids が 1回で 引ける
★⑨ ★新台帳0 ／ ★口0増 ／ ★保存欄0増 ／ ★新しい名前（定数・関数・欄）の数を ★報告する
★★⑩ ★★`HUMAN_APPROVERS` と ★`INTERIM_APPROVERS` は ★★bytes 不変（★★本件は 承認の道を 触らない）
```

## 7. ★注意

```
★★これは ★★『2DER が 自分で 権限を 発生させる』仕組み ―― ★★Taka の権限を 委譲する物では ない
   （★Taka 逐語『委譲ではなく、憲法に従って 2DER 自身が 権限を発生させる』）。
★★層3 は ★★常に Taka=★★固定条項 ／ ★材料が 無い物は ★層3へ 落ちる（★fail-closed）。
★★`tests_run`（★人が書いた文）は ★★★1箇所も 読まない=★★参考情報の ままにする。
★★本番配線 ∴ ★worker には 書かせない=★Claude(IMPL) が 書く ／ ★行数を 報告 ／
   ★★2DER の実績に 数えない。
```
