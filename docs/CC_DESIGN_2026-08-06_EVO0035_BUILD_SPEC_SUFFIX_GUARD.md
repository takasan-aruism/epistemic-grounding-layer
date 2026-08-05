# 【BUILD SPEC】`EVO-0035` — **★書き先の名前を検査する（★止める／★既定へ落とさない）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-06 03:1x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.15）** ／ 親: `ITEM-2DER-EVO-0035`
- **★v1.8 の宣言**: **★核は在る・1件**（`is_valid_suffix`＝純関数）→ **★2DER 工程 1 になりうる**
- **★私の予告**: ★worker の行数は書かない ／ ★Claude の配線 **2〜4行**（★呼んで ★止める）
- **★新台帳0・★新エンドポイント0・★新しい計器0**

---

## 1. ★いま何が起きるか（★実測・MGR 逐語）

```
★`egl/structure/s_account_axes.py:26-27`:
    SUFFIX = os.environ.get("ACCOUNT_AXES_SUFFIX", "v1").strip() or "v1"
    OUT_AXES = os.path.join(STRUCT, "ACCOUNT_AXES_%s.json" % SUFFIX)
★★∴ ★環境変数の中身が ★そのまま ★書き先の名前へ入る。
★★★`.strip() or "v1"` は ★空白だけの指定を ★★黙って `v1` へ落とす
   ＝ ★★「別名に書いたつもりで ★v1 を上書きする」形が ★作れる。
★★★★これが ★本件で ★塞ぐもの（★止める。★既定へ落とさない）
```

## 2. ★★契約

**★依頼文**
```
書き先の版名が使えるかを判定する純関数 impl.is_valid_suffix を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
suffix = 判定したい版名
戻り値 = bool

・suffix が str の時だけ判定する。str 以外は False。
・使ってよい文字は 半角の英字（a-z A-Z）・半角の数字（0-9）・下線（_）だけ。
  ALLOWED: この3種のいずれかだけで出来ている文字列。
・長さは 1 文字以上 32 文字以下。
・上のすべてを満たす時だけ True。満たさない時は False。
・★空文字は False（★既定へ落とす判断は ここでしない）。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def is_valid_suffix(suffix):
    # <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

**★封印試験（★8本・★通す例と止める例を 逐語で）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

def test_v1_is_allowed():
    """★既定の版名が ★通ること"""
    assert impl.is_valid_suffix("v1") is True

def test_v3_is_allowed():
    """★本日 実際に使った版名(★MGR が SUFFIX=v3 で走らせた)"""
    assert impl.is_valid_suffix("v3") is True

def test_underscore_is_allowed():
    assert impl.is_valid_suffix("exp_2026") is True

def test_empty_string_is_rejected():
    """★空文字は ★止める（★既定へ落として 黙って書き続ける形を 作らない）"""
    assert impl.is_valid_suffix("") is False

def test_path_traversal_is_rejected():
    """★書き先を ★別の場所へ 向ける形は ★止める"""
    assert impl.is_valid_suffix("../etc/passwd") is False

def test_space_is_rejected():
    assert impl.is_valid_suffix("v1 v2") is False

def test_too_long_is_rejected():
    assert impl.is_valid_suffix("a" * 33) is False

def test_non_string_is_rejected():
    assert impl.is_valid_suffix(None) is False
<<<2DER:END>>>
```

## 3. ★Claude の配線（★2〜4行）

```python
# s_account_axes.py:26 の直後 — ★止める。★既定へ落とさない。
SUFFIX = os.environ.get("ACCOUNT_AXES_SUFFIX")
if SUFFIX is None:
    SUFFIX = "v1"                                   # ★未設定は 既定（★MGR 受入(2)）
elif not is_valid_suffix(SUFFIX):
    raise SystemExit("ACCOUNT_AXES_SUFFIX が使えません: %r（英数字と下線・1〜32文字）" % SUFFIX)
```

```
★★`.strip() or "v1"` は ★外す ―― ★空白だけの指定が ★★黙って v1 を上書きする形を ★作るため
★★★`OUT_MEMB` も ★同じ SUFFIX を使う（★軸と membership が ★別の版に散らない）
```

## 4. 受入（★MGR の3点 ＋ 私の2点）

```
★(0) ★worker が書く（★Claude は本文0行）・★8本 全通
★(1) ★★通す例と ★止める例を ★逐語で 1本ずつ 実際に走らせて示す
     （★例: `ACCOUNT_AXES_SUFFIX=v9` → 走る ／ `ACCOUNT_AXES_SUFFIX=../x` → ★その場で止まる）
★(2) ★`ACCOUNT_AXES_SUFFIX` を ★渡さない時に ★`v1` のままであること
★(3) ★★`ACCOUNT_AXES_v1.json` と `ACCOUNT_MEMBERSHIP.jsonl` の ★blob が ★同じであること
     ★逐語 `880c11212cbdf7f28fe6bbc104ea598a522342e3` / `6393101f3862d6b4249a9956eb6149da9ba6c220`
★★(4) ★止まった時に ★★何も書かれていないこと（★途中まで書いて止まる形を 作らない）
★★(5) ★`OUT_MEMB` も ★同じ SUFFIX を使っていること（★軸だけ別名になる形を 作らない）
★(6) ★sha256 一致 ／★(7) ★Claude の配線行数 ／★(8) ★戻せる ／★(9) ★61本を走らせない ／★(10) ★commit しない
★★★★★予告を投入前に書く: ★行数 ／ ★(1) の2例で 期待する挙動
```

## 5. ★★これで防げないこと（★先に言う）

```
★★使える文字だけで出来た ★★`v1` を ★人が渡せば、★★v1 は ★上書きされる。
   ＝ ★★この検査は ★『名前の形』を見るだけで ★『上書きしてよいか』は ★見ていない。
★★★上書きを 防ぎたいなら ★別の1件（★例: 既存ファイルが在る時は 止める）＝ ★本件では 作らない。
★★★★∴ ★★『v1 が守られるようになった』とは ★書かない。★書けるのは ★『名前の形を検査するようになった』だけ。
```

## 6. 禁止

```
★不正な値を ★既定へ落として ★走り続ける（★止める）／ ★`.strip() or "v1"` を ★残す
★英数字と下線の外を ★通す（★ハイフン・ドット・スラッシュも ★通さない）
★`OUT_AXES` だけ ★別名にする（★`OUT_MEMB` も 同じ版に）
★★『v1 が守られる』と書く（★§5）／ ★新しい台帳・エンドポイント・計器を作る
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
