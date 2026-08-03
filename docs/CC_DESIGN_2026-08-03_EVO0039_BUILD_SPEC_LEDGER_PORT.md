# 【BUILD SPEC】`EVO-0039` — **★2DER 工程は 0。★全部 Claude の配線と申告する**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-03 22:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.10）** ／ **★9項目 確認済（★§6）** ／ 親: `ITEM-2DER-EVO-0035`
- **★v1.8 の宣言**: **★核は無い。★この単位の 2DER 工程は 0**（★MGR の裁定と一致・★隠さない）
- **★私の予告（★前回の不備の是正）**: **★Claude の配線 ★12〜20行**／★新しい台帳 0／★新しいエンドポイント 0
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★条件(b)「既存の流儀に乗せられるか」を先に見た → **★乗る**

```
★`LEDGER_REGISTRY.jsonl` の1行は ★`ledger_id` を持つ（`s10_ledger_registry.py:269` 逐語 `"ledger_id": key`）
★★∴ ★1件は ★`/api/resolve?id=<ledger_id>` の ★既存の流儀に ★そのまま乗る（★`ART-`/`CHG-`/`RTHREAD-` と同じ）
★★★一覧は ★`/api/roadmap` と同じ形の ★既存 view で足りる（★`webui.py:700-702` の流儀）
★★★★★∴ ★新しいエンドポイントを ★1つも作らない
```

**★但し ★`ledger_id` の書式を ★確かめていない【★未確認】** — ★`resolve` は ★prefix で分岐する ∴ **★実装が最初に ★1件の `ledger_id` を逐語で確かめ、★prefix で識別できなければ ★そこで止めて報告すること**（★書けるが引けない形を作らない）。

## 2. やること（★2箇所・★全部 Claude）

### 2-1. ★一覧（★`roadmap_view` と同じ形）
```python
# twoder/webui.py — ★roadmap_view の隣に1関数
def ledger_view():
    """EVO-0039: 台帳の一覧を読むだけ(read_only)。★新しい台帳を作らない=既存 LEDGER_REGISTRY を出す。"""
    import json as _j, pathlib as _p
    p = _p.Path("/home/takasan/egl/structure/LEDGER_REGISTRY.jsonl")
    if not p.exists():
        return {"ledgers": [], "count": 0, "readable": False, "read_only": True}
    rows = [_j.loads(l) for l in p.read_text().splitlines() if l.strip()]
    out = [{"ledger_id": r.get("ledger_id"), "path": r.get("path"), "repo": r.get("repo"),
            "rows": r.get("rows"), "liveness": r.get("liveness"), "role": r.get("role"),
            "purpose": (r.get("purpose_raw") or {}).get("genesis_subject")} for r in rows]
    return {"ledgers": out, "count": len(out), "readable": True, "read_only": True}
# GET の分岐を1行
        if u.path == "/api/ledgers":
            return self._send(ledger_view())
```
```
★★★`readable: False` と ★`count: 0` を ★分ける（★「無い」と「読めない」を混ぜない・★`/api/receipt` の流儀）
★★★★中身を ★作らない・要約しない（★`purpose` は ★`genesis_subject` を ★raw のまま）
```

### 2-2. ★1件（★`/api/resolve` に分岐1つ）
```python
# twoder/ids.py — ★`RTHREAD-` の隣
        if rid.startswith("<★実装が §1 で確かめた prefix>"):
            from twoder import <既存 or webui の ledger_view を使う形>   # ★新しいモジュールを作らない
            ...  # ★該当1件を返す。★無ければ None（★空 dict を返さない）
```
```
★★★prefix が ★識別に使えなければ ★★§1 のとおり ★止めて報告（★`resolve` に ★曖昧な分岐を足さない）
```

## 3. ★読む口と書く口（★対で名指し・規律 v1.1）

```
★書く口 : ★`egl/structure/s10_ledger_registry.py --apply`（★既存・★決定論・★本件では ★呼ばない）
★読む口 : ★`GET /api/ledgers`（★一覧）／★`GET /api/resolve?id=<ledger_id>`（★1件）
★★★書く口は ★本件で ★1文字も触らない（★再生成は ★別の作業）
```

## 4. ★★受入（★裁定の指定どおり）

```
★(1) ★`GET /api/ledgers` が ★件数と ★各台帳の目的を返す。★件数を ★逐語で書く
     ★★状況表の「55 ledgers」と ★合うか合わないかを ★そのまま書く（★合わなければ ★合わないと書く）
★(2) ★★陰性対照（★私が EVO-0039 の note で予告していたもの・★ここで実行する）:
     ★既知の台帳を ★1本 隠して ★『抜けている』と分かること。
     ★★方法=★台帳ファイルを触らない。★`ledger_view` に ★一時的に1件を除くのではなく、
     ★★★`--check` の ★既存の突合（★s10 が ★実ファイルを走査して行を作る）を使い、
     ★★★★★★★実装が ★『隠す手段が無いなら 無いと書いて止まる』（★捏造した対照を作らない）
★(3) ★★Claude の配線行数を申告（★2DER 工程0 ∴ ★全部 Claude の行数）
★(4) ★戻せる ／ ★(5) ★61本を走らせない（★走らせた名前を書く）
★★★★(6) ★『2DER が担当した』と ★★書かない（★裁定の逐語・★この単位は 0 と宣言済み）
★★★★★予告を投入前に書く: ★配線の行数 ／ ★(1) の件数の見込み
```

## 5. ★★これで直らないこと（★先に言う）

```
★一覧が読めても ★『既存を読んでから作る』が ★自動で守られるわけではない ―― ★読むのは ★我々である。
★★∴ ★本件の効果は ★「直読へ流れる理由が1つ減る」まで。★★「守られるようになった」と ★書かない
★★★台帳の直読を試みた回数（★累計8）が ★減るかどうかは ★★測っていない【★未確認】。
   ★★★★減ったかは ★次の単位以降で ★状況表の数字を ★見ればよい（★新しい計器を作らない）
```

## 6. ★9項目（私の分）
```
1 置いたなら読めるか＝★受入(1)(2) は ★front door から測る
2 読めるなら書けるか＝★§3 で ★書く口(`--apply`)を名指しし、★本件では触らないと明記
3 理由を捨てない＝★★`readable: False` と `count: 0` を ★分ける（★§2-1）
4 作っていないのでは＝★★一覧は ★既に在る（`LEDGER_REGISTRY.jsonl`）。★無いのは ★読む口だけ
5 走ったか＝★受入(1) は ★実際に叩いて件数を書く
6 名前＝★`ledger_id` / `liveness` / `role`（★`s10` の既存欄。★改名しない）
7 依頼と試験の矛盾＝★成果物を作らない ∴ 該当なし
8 計器が自分を数えないか＝★受入(1) は ★状況表の 55 と ★突き合わせる（★独立2経路）
★9 増える代わりに廃止＝★★「台帳を直読しようとしてフックに拒まれる」経路を ★減らす。
   ★★但し ★§5 のとおり ★★「廃止した」と ★書かない（★累計8 が減るかは ★未測）
```

## 7. 禁止
```
★新しい台帳・新しいエンドポイント（★`/api/ledgers` 以外）を作る ／ ★`s10 --apply` を走らせる
★`purpose` を要約・翻訳する（★raw のまま）／ ★「無い」と「読めない」を同じ欄に入れる
★捏造した陰性対照を作る（★隠せないなら ★隠せないと書いて止まる）
★『2DER が担当した』と書く ／ ★61本を走らせる ／ ★commit する
★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
