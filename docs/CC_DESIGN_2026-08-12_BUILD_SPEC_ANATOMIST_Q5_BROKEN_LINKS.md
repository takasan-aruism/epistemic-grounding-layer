開発者規律 確認済(v1.0)

# 【BUILD SPEC】★SYSTEM_ANATOMIST ★問い⑤だけ ―― ★記録が 途切れている区間は どこか

宛: IMPL ／ 発: DESIGN ／ 2026-08-12 03:35 ／ 台帳: `ITEM-2DER-EVO-0065`
出所: MGR 基本設計（03:0x）＋ **Taka 訂正 03:15**「★ただ台帳調べにいくだけの Worker ではない／★経路表に関係する Worker」

**★★完成の線: ★内側**（★役割②「正しく機能しているかを確認する」の 最小の1問）
**★★切る所: ★★この1問で 切る**（★5問 揃うまで 続けない）

---

## 1. ★★作る物（★★口 だけ・★計算は 写さない）

```
★★計算は ★既に 在る = ★`twoder/route_observed.py` の `plus_minus`（★昨日 作った）
★★無いのは = ★★Manager が ★『問い』として 引く 口
★★∴ ★★既存の `GET /api/control` に ★★1欄 足す（★★front door の 口は 0増）

★★`anatomist`: {
   ★"question": "Q5_BROKEN_LINKS",
   ★"answer": [ …下の 1行の形… ],
   ★"total_segments": 18,
   ★"as_of": ★引いた時刻,
   ★"unreadable": {count, ids}          ← ★引けなかった分（★0件なら 0件）
 }
```

## 2. ★★答えの形（★★配線の言葉だけ・★★item 名や 時刻を 混ぜない）

```
★1件 = ★{
   ★"segment": "S07",
   ★"from": "submit",                    ← ★ROUTE の from
   ★"to": "EGL admission",               ← ★ROUTE の to
   ★"sends": ["admission_payload"],      ← ★ROUTE の sends（★新しい値を 作らない）
   ★"handed_over": "EMPTY",              ← ★＋側の 3値
   ★"received": "PRESENT",               ← ★−側の 3値
   ★"missing_side": "HANDOFF"            ← ★★どちらが 欠けているか（★HANDOFF / RECEIPT / BOTH）
 }
★★『どこが 抜けると 止まるか』に ★そのまま 答える形（★Taka 逐語）
★★★`missing_side` は ★★3値から 機械で 決まる（★人が 書かない・★LLM 0回）
```

## 3. ★★同時に 直す（★★私の 定義の 重なり・★1語 減らす）

```
★★升目で 書く（★★1つの升目に 2つの名前を 置かない）
   ★＋PRESENT / −PRESENT → ★`LINKED`
   ★＋PRESENT / −無      → ★`SURPLUS_PLUS`      （★出したのに 受け取られない）
   ★＋無 / −PRESENT      → ★`UNOBSERVED_HANDOFF`（★受け手は 動いたが 渡した記録が 無い）
   ★＋無 / −無           → ★`NEITHER_OBSERVED`
★★★`UNMET_MINUS` は ★★`SURPLUS_PLUS` の 別名 ＝ ★★★廃止する（★規律9＝★増やす時に 減らす）
★★実測（★2026-08-12 03:20）= ★いま `UNMET_MINUS` に 7件 入っている ＝
   ★★中身は ★＋EMPTY / −PRESENT ＝ ★★★本来 `UNOBSERVED_HANDOFF`
   ＝ ★★★名前が 意味と 逆に 付いている ∴ ★同じ変更で 直す
```

## 4. ★★受入（★★固定値を 書かない＝★数が 走行のたびに 動くため）

```
★★① ★`GET /api/control` の `anatomist.answer` が ★★配線の言葉だけで 返る
     ―― ★★`segment` / `from` / `to` / `sends` / `handed_over` / `received` / `missing_side`
     ―― ★★★item 名・時刻・人の文が ★★0件（★機械で 確かめる）
★★② ★★同時刻に 2回 引いて ★★同じ答え（★★固定値では 受けない＝★走行で 動くため）
★★③ ★`answer` の件数 ＋ `LINKED` の件数 = ★★★18（★母数が 合う＝★取りこぼし 0）
★★④ ★`missing_side` が ★3語のどれか（★`HANDOFF` / `RECEIPT` / `BOTH`）＝ ★空の行 0件
★★⑤ ★★`UNMET_MINUS` が ★★どこにも 出ない（★★廃止の 確認）／
     ★`by_verdict` に ★4語とも 欄が 在る（★0件でも 消さない）
★★⑥ ★★LLM 0回（★★この問いは 決定論で 足りる＝★Qwen を 呼ばない）
★★⑦ ★front door の 口 0増 ／ ★新台帳0 ／ ★★新しい部品を 作らない（★既存の `plus_minus` を 呼ぶ）
★★⑧ ★★呼び手が 0件の 部品を 作らない（★★MGR 条件・★本日 9回 出た形）
★★⑨ ★`/api/control` が ★1秒以内（★退行）
```

## 5. ★★やらないこと（★★1問で 切る）

```
★★①②③④の 問いを ★同じ変更で 作らない（★★5問 揃うまで 続けない＝MGR 条件）
★★Worker を 常駐させない（★★引く側は Manager＝★MGR 裁定）
★★台帳へ 書かない ／ ★git を 触らない ／ ★source を 読ませない（★Taka 逐語）
★★『止まっている item』を 出さない ―― ★★★それが『ただ台帳調べ』＝ ★Taka が 否定した形
```

## 6. ★★権限（★1行も 増やさない）

```
★段 = ★層1 `OBSERVE` ／ ★決定 = `AUTO_APPROVED` ／ ★理由 = ★参照のみ・書かない
★★既存の 22/22 の判定に そのまま 乗る ＝ ★★Taka の操作は ★0回 増える
```
