# 【BUILD SPEC】`resolve` が履歴を返す（★読み手だけ直す・可逆）

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-02 03:3x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.3）** ／ **★9項目 確認済（★§5）**
- **★裁定の在り処**: `ITEM-2DER-EVO-0022` の `status_note`（逐語:「★読む口が最新1件しか返していないのを直す…最小・可逆で resolve が履歴を返せるようにする(既存の口に history を足す形)…★受入=EVO-0031 に私が書いた裁定5件が front door から全部 読める」）

---

## 1. ★経路（★書く前に叩いた）
```
★`GET /api/resolve` → ★`webui.resolve_view`（`webui.py:246-250` 逐語）
   → ★`IDS.resolve(rid)`（`twoder/ids.py:131-133` 逐語: `if rid.split("-",1)[0] in ("ROADMAP","PHASE","ITEM","AMEND"): return RM.resolve(rid)`）
   → ★`roadmap_registry.resolve`（`:81-87` 逐語: `for e in _read(): if _idkey(e)==rid: latest=e` ＝ ★上書き）
★★★∴ ★直す先は ★2箇所（★台帳側に履歴関数を1つ・★`resolve_view` に欄を1つ）。★`ids.py` は ★触らない
★★★★★書き手は ★正しい（★`_append` は追記のみ）∴ ★★台帳に手を入れない
```

## 2. やること

### 2-1. `twoder/roadmap_registry.py` に1関数
```python
def history(rid, limit=50):
    """★rid の全エントリを ★古い順に返す（★追記されたものを ★そのまま）。★limit で末尾から切る。"""
    hs = [e for e in _read() if _idkey(e) == rid]
    return hs[-limit:] if limit and len(hs) > limit else hs
```

### 2-2. `twoder/webui.py:246-250` に1欄
```python
def resolve_view(rid):
    from twoder import ids as IDS
    rec = IDS.resolve(rid) if rid else None
    ★hist = None
    ★if rid and rid.split("-", 1)[0] in ("ROADMAP", "PHASE", "ITEM", "AMEND"):
    ★    from twoder import roadmap_registry as RM
    ★    hist = RM.history(rid)
    return {"id": rid, "resolved": rec is not None, "record": rec, ★"history": hist, "read_only": True}
```
```
★★`record` は ★変えない（★既存の読み手が壊れない）。★★`history` を ★足すだけ
★★★戻し方: ★足した2箇所を消す。★★可逆
★★★★`ITEM` 以外（`TASK-`/`DE-` 等）は ★`history: null` のまま ＝ ★今回の対象外（★1件進めるために2件増やさない）
```

## 3. 受入
```
★(1) ★`GET /api/resolve?id=ITEM-2DER-EVO-0031` の ★`history` に ★★MGR の裁定5件が★全部 在る
     ★★数える: ★`status_note` に「裁定」を含む要素の件数 ★≧5 ／ ★逐語で読める
★(2) ★`record` は ★従来どおり ★最新1件（★変わっていない）
★(3) ★戻せる（★2箇所を消したら ★`history` が消え ★元に戻る）——★戻して確かめ、★また足す
★(4) ★★応答が大きくなりすぎないこと——★`limit=50` が効いていることを ★1件で確かめる
★★★★★予告を投入前に書く: ★(1) の件数 ／ ★変更行数 ／ ★応答の字数
```

## 4. ★増える代わりに廃止（★裁定の逐語）
```
★★「★.md に裁定を書く運用」を ★★完全に畳む（★v1.3 で縮小済みの残り）。
★★★本件が通ったら ★★裁定は ★台帳だけに書く。★`.md` に裁定を置かない。
★★★★★通らなければ ★廃止しない（★嘘を書かない）
```

## 5. ★9項目（私の分）
```
1 置いたなら読めるか＝★`GET /api/resolve` の `history`（★受入(1)）
2 読めるなら書けるか＝★書き手は既存（`_append`・追記）★該当済
3 理由を捨てない＝★該当なし（★本件は読み手の追加）
4 作っていないのでは＝★★履歴は ★既に台帳に在る（★`_read()` が全件 返す）∴ ★作らない・出すだけ
5 走ったか＝★実装が webui 再起動を確かめる
6 名前＝★`history` は ★新語だが ★状態語でも台帳でもない（★応答の欄）
7 依頼と試験の矛盾＝★本件は機構 ∴ 該当なし
8 計器が自分を数えないか＝★★私が数えるのは ★MGR が書いた裁定 ∴ ★自分の書き込みではない
★9 増える代わりに廃止＝★★§4（.md への裁定を畳む）
```

## 6. 禁止
```
★`record` の中身を変える ／ ★`ids.py` を触る ／ ★台帳（`_append`）に手を入れる
★`TASK-`/`DE-` 等に `history` を広げる（★対象外）／ ★新しいエンドポイント・状態語・台帳を作る
★commit する ／ ★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
