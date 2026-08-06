# 【BUILD SPEC】`EVO-0049` V5 — **★試験は1字も変えない ／ ★変えるのは 依頼文の 形だけ**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-06 20:2x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.15）** ／ 台帳: `ITEM-2DER-EVO-0049`
- **★核0（★関数は 同じ・★試験は 同じ）／ ★新台帳0 ／ ★新エンドポイント0 ／ ★Claude の配線 0行**
- **★V4 との差分は ★依頼文の 1ブロックだけ**（★骨格 同一・★封印試験 ★bytes 同一 ／ sha256 `c75203330c7693dbda2958c1fac425eeb4d9c64f775c7c39cd04a76d706ae27e`）

---

## 1. ★★なぜ V5 が 要るのか（★原因は 私に在る）

```
★実測 = ★live 4標本(v2×1 / v3×2 / v4×1)で ★9本中 ★つねに 同じ1本だけが 落ちた
        （★`test_binder_present_wins_even_without_context` ／ ★他8本は 毎回 通る）
★★私が その場で 再現した = ★依頼文を ★『上から並んだ番人列』として ★平らに読む実装を 書くと
        ★★1 failed / 8 passed ／ ★落ちる試験も ★同一。
★★★∴ ★原因は ★worker の品質ではなく ★★私の依頼文の 形である（★入れ子が 伝わらない）。
★★★★V4 の該当箇所(★逐語) = 『★ここから先は "binder_present" が False の場合:』＋★字下げ
      ―― ★この入れ子の内側に在った ★"context_supplied" の型検査が ★先頭へ 持ち上がり、
         ★`binder_present=True` でも ★NOT_ASSESSED を 返す。
★★★★★∴ ★版を 増やしても 直らない（★形の問題であって ★量の問題では ない）。
```

## 2. ★★依頼文（★V5・★入れ子を 開いた）

```
signals から intent の読み取り状態を1語で返す純関数 impl.intent_status_from_signals を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
signals = dict（preflight_gate が作る警告の理由。関係する欄は
          "binder_present": bool, "context_supplied": bool）
戻り値 = str。NOT_ASSESSED / CLEAR / INDETERMINATE_NO_CONTEXT / AMBIGUOUS の4語のいずれか。
         他の語を作らない。

★読み方は4通り。★上から順に、最初に当てはまった1つで決める。

(1) signals が dict でない → "NOT_ASSESSED"
(2) signals["binder_present"] が True → "CLEAR"
    ★この時、他の欄は 読まない。★"context_supplied" が 何であっても、無くても、"CLEAR"。
(3) signals["binder_present"] が False → "context_supplied" を見る:
        True  → "AMBIGUOUS"（文脈は在るのに束縛先が無い）
        False → "INDETERMINATE_NO_CONTEXT"（文脈が渡されていない）
        上の2つ以外（bool でない・欄が無い） → "NOT_ASSESSED"
(4) (1)(2)(3) のどれにも当てはまらない → "NOT_ASSESSED"
```

**★骨格（★V4 と 同一）**
```
<<<2DER:SKELETON>>>
def intent_status_from_signals(signals):
    # <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

**★封印試験（★V4 と ★bytes 同一・★9本・★1字も 変えない）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

# 実物の signals(逐語): matched_surface / binder_present / binder_reason /
#                       binder_candidates / context_supplied / surface_rule / match_mode / binder_rule
BASE = {"matched_surface": "それ", "binder_present": False, "binder_reason": "no-binder",
        "binder_candidates": [], "context_supplied": False,
        "surface_rule": "SURF-RULE-001", "match_mode": "SENTENCE_INITIAL_BARE",
        "binder_rule": "BIND-RULE-001"}

def test_no_context_is_indeterminate():
    """★context_supplied が False の時は ★INDETERMINATE_NO_CONTEXT を返す"""
    assert impl.intent_status_from_signals(BASE) == "INDETERMINATE_NO_CONTEXT"

def test_context_but_no_binder_is_ambiguous():
    """★文脈が在り ★束縛先が空の時は ★AMBIGUOUS を返す"""
    assert impl.intent_status_from_signals(dict(BASE, context_supplied=True)) == "AMBIGUOUS"

def test_binder_present_is_clear():
    assert impl.intent_status_from_signals(dict(BASE, binder_present=True)) == "CLEAR"

def test_binder_present_wins_even_without_context():
    """★束縛先が在る時は ★binder_present だけで ★CLEAR を決める（★順序が効くこと）"""
    s = dict(BASE, binder_present=True); s.pop("context_supplied")
    assert impl.intent_status_from_signals(s) == "CLEAR"
    assert impl.intent_status_from_signals(dict(BASE, binder_present=True,
                                                context_supplied="yes")) == "CLEAR"

def test_non_dict_is_not_assessed():
    assert impl.intent_status_from_signals(None) == "NOT_ASSESSED"

def test_missing_binder_field_is_not_assessed():
    s = dict(BASE); s.pop("binder_present")
    assert impl.intent_status_from_signals(s) == "NOT_ASSESSED"

def test_missing_context_field_is_not_assessed():
    """★binder_present が False で ★context_supplied の欄が欠けている時は ★NOT_ASSESSED を返す"""
    s = dict(BASE); s.pop("context_supplied")
    assert impl.intent_status_from_signals(s) == "NOT_ASSESSED"

def test_all_four_words_are_reachable():
    got = {impl.intent_status_from_signals(None),
           impl.intent_status_from_signals(dict(BASE, binder_present=True)),
           impl.intent_status_from_signals(BASE),
           impl.intent_status_from_signals(dict(BASE, context_supplied=True))}
    assert got == {"NOT_ASSESSED", "CLEAR", "INDETERMINATE_NO_CONTEXT", "AMBIGUOUS"}, got

def test_never_outside_the_four():
    for s in (None, "x", {}, BASE, dict(BASE, context_supplied=True),
              dict(BASE, binder_present=True), dict(BASE, binder_present="yes")):
        assert impl.intent_status_from_signals(s) in (
            "NOT_ASSESSED", "CLEAR", "INDETERMINATE_NO_CONTEXT", "AMBIGUOUS")
<<<2DER:END>>>
```

## 3. ★★私が 先に 確かめたこと（★走行を 使わずに）

```
★新しい依頼文を ★2通りに 読んだ実装を ★私が 書いて 走らせた:
   ★(a) 素直に読む（★早期 return）      → ★★9本 全通
   ★(b) ★平らな番人列として読む(★V4 を壊した読み方) → ★★9本 全通
★★∴ ★★新しい形には ★持ち上がる番人が 無い ―― ★どちらの読み方でも ★同じ答えに なる。
★★★これが ★V5 の 中身の すべてです（★他は 1字も 変えていません）。
```

## 4. ★★同じ契約で 2標本目を 引く（★MGR 04:20 §5(1) への 回答・★新しい仕組み 0）

```
★MGR の問い(逐語) = 『★同じ契約の ★2標本目を 取る口が ありません』
   ★実測された症状 = ★同じ raw を もう一度 投入 → ★同じ task_id が 返り ★走行が 増えない。
★★答え = ★★口は ★もう 在ります。★根拠(★逐語):
   ★`submit.py:531` → `dw_task = "TASK-2DER-" + sha1(★raw_input 全体).hexdigest()[:8].upper()`
   ★`contract_seal.extract_contract` → ★読むのは ★目印(`<<<2DER:SKELETON>>>` / `<<<2DER:IMMUTABLE_TESTS>>>`)の ★内側だけ
★★★∴ ★★目印の 外側を 1字 変えれば、★task_id は 変わり ★契約は bytes 同一のまま。
★★★★具体= ★投入文の 末尾に `★標本: 2` の 1行を 足す（★目印の 外）。
      ★確かめ方 = ★`/api/resolve` の `sent.sha256` が ★標本間で ★一致すること（★契約が 同じ証拠）。
```

## 5. ★★受入（★★1走行では 判定しない）

```
★(1) ★★標本を ★3つ 取る（★§4 の方法・★同一契約であることを `sent.sha256` の一致で 示す）
★(2) ★★私の予告(★先に 書きます) = ★★『落ちるとしても
     ★`test_binder_present_wins_even_without_context` では ない』
     ★★ここが また 落ちたら ★★私の原因特定が 誤りです（★その時は 私に 戻してください）
★(3) ★全通した標本数を 書く（★★『何本 通った』でなく ★『何標本 中 何標本』）
★(4) ★★1走行の数字で ★版の優劣を 書かない（★本日の規律）
★(5) ★Taka 注意(a) に従い ★A/B とは ★混ぜない（★本件のみ 単独で 入れる）
★(6) ★戻せる ／ ★(7) ★61本を走らせない ／ ★(8) ★commit しない ／ ★(9) ★twoder 配下で python を動かさない
```

## 6. ★★私が 言っていないこと

```
★『V5 なら 通る』―― ★★予告していません（★§5(2) で 予告したのは ★落ち方の 場所だけ）。
★『worker が 良くなった』―― ★★worker には ★何も していません。
★『V4 が 間違いだった』―― ★★規則の 中身は 同じです。★変えたのは ★形だけ。
★『4標本で 因果が 決まった』―― ★因果を 決めたのは ★★私が 再現した実装であって ★標本数では ありません。
```
