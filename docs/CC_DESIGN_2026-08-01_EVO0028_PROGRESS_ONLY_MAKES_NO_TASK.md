# 【BUILD SPEC / `EVO-0028`】進捗だけの投入で **★task を作らない** ／ **★滞留6件は畳めない（理由つき）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-01 08:0x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.0 / 2026-07-31）** ／ **裁定**: `D-205` §2（ACTIVE＝`EVO-0028`・条件3つ）
- **この .md がまだ .md である理由**: 指示を台帳へ渡す口が無いため（★`EVO-0022` / C-2）
- **★増える管理対象 0** ／ **★私はコードを1行も変えていない**

---

# 1. ★原因（★決定論・逐語）

```
★進捗だけの投入は ★`OBSERVE_CURRENT_STATE` に分類される（★実測: `TASK-2DER-24EF3F6E` ほか）
★★`twoder/submit.py:434` 逐語: `W.create_task(_obs_task, "2DER", raw_input, _obs_kp, ts, "2der-conductor")`
   ＝ ★観測経路は ★★無条件に task を作る。★中身が進捗の記録だけでも作る。
★★★∴ ★進捗を1件 書くたびに ★「★Claude が PLAN するのを待つ依頼」が1件 増える。
★★★★実測: ★`CREATED` のまま滞留 ★6件（`24EF3F6E` `786DC614` `5483F350` `322B1B62` `1F4C8C42` `587AFD37`）
```

---

# 2. ★条件①: **進捗だけの投入では task を作らない**（★1箇所）

## 2-1. ★判定（★決定論。★LLM を通さない）
```
★★「進捗だけ」＝ ★次の3つが★同時に成り立つとき:
   ① ★`progress_seal.extract_progress(raw_input)` が ★dict を返す
   ② ★`contract_seal.extract_contract(raw_input)` が ★`None`（★契約が無い）
   ③ ★★`<<<2DER:PROGRESS>>>` 〜 `<<<2DER:END>>>` を★取り除いた残りに ★非空白文字が★1つも無い
★★★③が肝である: ★本文が在れば ★それは依頼でもある ∴ ★従来どおり task を作る（★fail-closed・安全側）
★★★★★迷ったら ★作る側に倒す。★★「作らない」を★広げない。
```

## 2-2. ★やること（★既に在る呼び出しの中だけ）
```python
# submit.py:214（_rec("RRI_REQUEST_TYPE", rt) の直後）＝ ★進捗処理が既に在る場所
_progress_only = bool(_prog) and _contract_is_none and _rest_is_blank   # ★§2-1 の3条件
_rec("PROGRESS_ONLY", _progress_only)          # ★判定を記録に残す（★後から数えられる）

# submit.py:434 と :490 の create_task を、フラグが立っていたら呼ばない
if not _progress_only:
    W.create_task(...)                          # ★既存の行はそのまま
else:
    _rec("DW_TASK_CREATE_RESULT", "SKIPPED: progress-only submit (EVO-0028)")
    _rec("DW_TASK_ID", None)                    # ★None は「作らなかった」。★空文字にしない
```
```
★★`contract_seal` / `progress_seal` / `set_status` / `_MAP` に ★手を入れない
★★★`extract_contract` は ★`submit.py:470`（DW 分岐の中）に在る ∴ ★:214 で使うなら ★もう1回 呼ぶか
   ★判定だけ先に取る。★★どちらでもよいが ★2回 呼ぶなら ★「2回 呼んだ」と報告に書く
```

# 3. ★条件②: **進捗は今までどおり書ける**
```
★`progress_write` は ★従来どおり返る（★`ok: true`）。★`set_status` / `register_item` の呼び出しは★動かさない。
★★★これが崩れたら ★C-1 の後退である ∴ ★受入で必ず確かめる。
```

---

# 4. ★★条件③: 滞留6件は **★畳めない**（★放置しない・消さない・★理由を書く）

```
★★調べた（★`dev-workcell/dw/workcell.py` 全数・打ち切り無し）:
   ★読み手は在る: `:185-186` 逐語 `elif ph == "BLOCK": state = "BLOCKED"`
   ★★★書き手は ★無い: `record_*` は ★`process_event` / `plan` / `generate` / `audit` /
      `disposition` / `regenerate` / `upper_review` の ★7つで、★★`BLOCK` を書く関数は ★0件
★★★∴ ★`CREATED` の task を ★`BLOCKED` へ畳む口が ★存在しない。
★★★★★これは ★本日 4度目の同じ形である（★`JUDGE_REQUIRED` が `_MAP` に無い ／
   ★`next_information_need` が停止時に書かれない ／ ★新規 ITEM の登記口が無い ／ ★本件）。
   ★★★＝ ★「読める形は在るが、★書く口が無い」。★偶然ではないと思われる。★私は原因を断定しない。
```

## 4-1. ★∴ 今回やること（★Taka 常設命令の形で書く）
```
★★畳めない ∴ ★★「畳む条件」と「いま足りないもの」を★併記して残す:
   ★畳む条件   : ★`BLOCK` を書く口ができること
   ★足りないもの: ★その口（★`record_block` に当たるもの）
★★★★今回は ★作らない（★規律9・★ACTIVE は1件）。★★`EVO-0028` の note に ★この2行を書く。
★★★★★★消さない・放置しない: ★6件は ★`CREATED` のまま残る。★★増えなくなるのが ★今回の成果である。
```

---

# 5. ★受入（★`D-205` §2 のまま。★緩めない）
```
★① ★`GET /api/tasks` の件数を ★投入の★前後で数え、★★増えないこと
★② ★同じ投入で ★`progress_write.ok = true`（★C-1 が後退していない）
★③ ★`DW_TASK_ID` が ★`None`（★「作らなかった」が記録に残る）
★④ ★★本文つきの投入（★進捗＋依頼文）では ★★従来どおり task が★作られること（★安全側の確認）
★★★★★投入前に予告を書く: ★前の task 件数 ／ 予想（★③④の別）／ 使う item id と status
```

# 6. ★手順 ／ 7. ★やってはいけないこと ／ 8. ★報告
```
【手順】① `GET /api/tasks` で件数を数え ★予告を書く → ② §2-2 の変更 → ③ webui 再起動
        → ④ ★進捗だけの投入1回 → ⑤ 件数を数え直す（★受入①）→ ⑥ `progress_write` を見る（★受入②③）
        → ⑦ ★本文つきの投入1回で ★task が作られることを確かめる（★受入④）
        → ⑧ ★`EVO-0028` の note に §4-1 の2行を書く（★front door から・★同じ口で）
【禁止】★`contract_seal`/`progress_seal`/`set_status`/`register_item`/`_MAP` に手を入れる
        ★`BLOCK` を書く口を作る（★別件・★今回やらない）／ ★滞留6件を消す
        ★新しい台帳・新しいマーカー・新しい状態語を作る ／ ★commit する
【報告】1 ★書いた行数 ／ 2 ★受入①〜④ ／ 3 ★予告の当否 ／ 4 ★`extract_contract` を2回 呼んだか
        5 ★滞留6件の件数（★増えていないこと）／ 6 ★`EVO-0028` の note に書いたか
★宛: 設計/監査(CC-α)。TYPE=BUILT
```

---
**決めたこと**: **①原因は `submit.py:434` の観測経路が無条件に `create_task` を呼ぶことで、進捗を1件 書くたびに待ち依頼が1件 増える。実測で `CREATED` 滞留は6件 ②条件①の判定は決定論で3つ同時——`extract_progress` が dict／`extract_contract` が `None`／マーカーを除いた残りに非空白文字が0。本文が在れば依頼でもあるので従来どおり task を作る（fail-closed・安全側）。迷ったら作る側に倒し「作らない」を広げない ③実装は既に在る呼び出しの中だけで、`_progress_only` を立てて `create_task` を飛ばし、`DW_TASK_ID` に `None` を残す（空文字にしない）④条件②は C-1 の後退を許さない。`progress_write.ok` が返り続けることを受入で確かめる ⑤★条件③——滞留6件は畳めない。`BLOCK` の読み手は `workcell.py:185-186` に在るが、`record_*` 7つの中に `BLOCK` を書く関数は0件だから ⑥これは本日4度目の「読める形は在るが書く口が無い」であり、偶然ではないと思われるが原因は断定しない ⑦∴ 畳む条件（`BLOCK` を書く口ができること）と足りないもの（その口）を併記して `EVO-0028` の note に残す。今回は作らない。6件は消さず `CREATED` のまま残し、増えなくなることが今回の成果である ⑧受入は4つで、本文つきの投入では従来どおり task が作られること（安全側）も確かめる。**
