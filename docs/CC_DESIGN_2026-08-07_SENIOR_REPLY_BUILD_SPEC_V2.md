# 【BUILD SPEC】`parse_senior_reply` V2 — **★実データ3標本で 契約を 確定する（★1/3 が 落ちていました）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-07 08:0x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: ★v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ 効く先＝4 の前段
- 前便: `CC_DESIGN_2026-08-07_AUDIT_SENIOR_REPLY_DRAFT.md`（★初稿の監査）
- **★核1（★同じ関数）／ ★新台帳0 ／ ★新エンドポイント0 ／ ★Claude の配線 0行**

---

## 1. ★★実データが 出したこと（★MGR が 3標本 取った・★逐語）

```
★(1) "PASS. 封印試験で8本中8本が通過しており、成果物 twoder/is_known_verdict.py が存在する。"
★(2) "PASS 封印試験で8本中8本が通過しており、成果物も存在するため。"
★(3) "PASS\n封印試験で8本中8本が通過し、成果物が指定された場所に存在するため。"

★★初稿の契約に そのまま 通すと:
   ★(2)(3) → PASS ／ ★★(1) → ★★UNKNOWN（★"PASS." の `.upper()` は "PASS." であって "PASS" ではない）
★★★∴ ★★実データの ★1/3 が ★黙って 人へ 回ります。
★★★★これは ★前便 §3 で 私が 挙げた危険（★『効かない』）が ★★1標本目で 現れた形です。
```

## 2. ★★直す所は ★1つだけ（★句読点の一覧は 作りません）

```
★初稿 = ★『先頭の語（半角スペースか改行まで）』を 判定の語と する
★★V2  = ★★『先頭の空白を除いた後、★そこから続く 半角英字だけ』を 判定の語と する

★★★これで 直る理由 = ★判定の語は ★英字で できている ∴ ★英字が 切れた所が 語の終わり。
   ★★句読点を 列挙しません（★"." "。" ":" を 数え上げると ★次に 別の記号が 来た時に また 落ちます）。
★★★★同時に 消えるズレ（★前便 §1 §2）:
   ★ズレ①（★根拠の 内側の空白が 潰れる）= ★`split()` を 使わない ∴ ★内側は そのまま 残る
   ★ズレ②（★全角スペースが 区切りに なる）  = ★『区切り』という考え方が ★無くなる
★★★★★守られる裁定（★変えません）:
   ★全角の判定語（"ＰＡＳＳ"）→ ★UNKNOWN ／ ★語の外（"APPROVED"）→ ★UNKNOWN
   ★根拠が 空 → ★UNKNOWN ／ ★前に飾りが付く（"**PASS**" / "判定: PASS"）→ ★UNKNOWN
```

**★私が わざと 直さない所（★理由つき）**

```
★(1) の根拠は ★". 封印試験で…" と ★先頭に 句点が 残ります。
★★直しません。★理由 = ★根拠は ★人が読む物であり、★先頭の1文字は ★意味を 変えません。
   ★★取り除くには ★句読点の一覧が 要り、★それは ★次の記号で また 破れます
     （★記憶『厳格さは リターンを示せ』）。
```

## 3. ★★契約（★依頼文・★V2）

```
上級監査の返答から 判定と根拠を取り出す純関数 impl.parse_senior_reply を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
text = 上級監査が返した文字列。
戻り値 = {"verdict": str, "reason": str}
         verdict は PASS / FAIL / UNKNOWN の3語のいずれか。他の語を作らない。

★読み方は5通り。★上から順に、最初に当てはまった1つで決める。

(1) text が str でない → {"verdict": "UNKNOWN", "reason": ""}
(2) text の先頭の空白を除いた後、そこから続く 半角英字（a-z A-Z）を つなげた物を「判定の語」とする。
    半角英字が 1文字も無い → {"verdict": "UNKNOWN", "reason": ""}
(3) 判定の語を 大文字にした結果が "PASS" でも "FAIL" でもない
    → {"verdict": "UNKNOWN", "reason": ""}
(4) 判定の語の 続きの部分から 前後の空白を除いた物が 空
    → {"verdict": "UNKNOWN", "reason": ""}
(5) 上のどれにも当てはまらない
    → {"verdict": 判定の語を大文字にした物, "reason": 続きの部分から 前後の空白を除いた物}

★続きの部分の 内側の空白は そのまま 残す（★改行も そのまま）。
★半角英字だけを 大文字にする。全角の文字は そのまま 扱う。
```

**★骨格（★初稿と同一）**
```
<<<2DER:SKELETON>>>
def parse_senior_reply(text):
    # <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

**★封印試験（★11本・★fixture は ★MGR が取った実データ）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

# ★実データ(2026-08-07 07:5x・同じ問いを3回・逐語)
R1 = "PASS. 封印試験で8本中8本が通過しており、成果物 twoder/is_known_verdict.py が存在する。"
R2 = "PASS 封印試験で8本中8本が通過しており、成果物も存在するため。"
R3 = "PASS\n封印試験で8本中8本が通過し、成果物が指定された場所に存在するため。"

def test_real_reply_1_gives_pass_when_a_period_follows_the_word():
    """★実データ1: 判定の語の直後に 句点が付く形（★初稿では UNKNOWN に落ちた）"""
    assert impl.parse_senior_reply(R1)["verdict"] == "PASS"

def test_real_reply_2_gives_pass_when_a_space_follows_the_word():
    assert impl.parse_senior_reply(R2)["verdict"] == "PASS"

def test_real_reply_3_gives_pass_when_a_newline_follows_the_word():
    assert impl.parse_senior_reply(R3)["verdict"] == "PASS"

def test_real_reply_2_keeps_the_reason_verbatim():
    assert impl.parse_senior_reply(R2)["reason"] == "封印試験で8本中8本が通過しており、成果物も存在するため。"

def test_inner_newline_is_kept_when_the_reason_has_two_lines():
    """★根拠の 内側の空白は そのまま 残す（★初稿の実装は ここで 畳んでいた）"""
    r = impl.parse_senior_reply("PASS 試験は通った\n成果物は repo に在る")
    assert r["reason"] == "試験は通った\n成果物は repo に在る", r

def test_fail_with_reason_gives_fail():
    r = impl.parse_senior_reply("FAIL 成果物が repo に在りません")
    assert r == {"verdict": "FAIL", "reason": "成果物が repo に在りません"}, r

def test_lowercase_gives_the_uppercase_verdict():
    assert impl.parse_senior_reply("pass 試験は通っています")["verdict"] == "PASS"

def test_empty_reason_gives_unknown():
    assert impl.parse_senior_reply("PASS") == {"verdict": "UNKNOWN", "reason": ""}
    assert impl.parse_senior_reply("PASS   ") == {"verdict": "UNKNOWN", "reason": ""}

def test_word_outside_the_two_gives_unknown():
    assert impl.parse_senior_reply("APPROVED 良さそうです") == {"verdict": "UNKNOWN", "reason": ""}

def test_fullwidth_word_gives_unknown():
    assert impl.parse_senior_reply("ＰＡＳＳ 試験は通っています") == {"verdict": "UNKNOWN", "reason": ""}

def test_decoration_before_the_word_gives_unknown():
    """★語の前に 記号や 前置きが 付く形は 受け取らない（★人へ回す）"""
    for t in ("**PASS** 通った", "判定: PASS 通った", "- PASS 通った", None, 3, ""):
        assert impl.parse_senior_reply(t)["verdict"] == "UNKNOWN", t
<<<2DER:END>>>
```

## 4. ★★受入（★口・欄・★id の3つ）

```
★(1) ★11本 全通（★worker が書く・★Claude は本文0行）
★(2) ★口 = `GET /api/resolve?id=TASK-…` ／ ★欄 = `artifact.name` と `found`
     ★id = ★★この契約を走らせた その走行の task（★空欄にしない）
     ★読める物 = `parse_senior_reply` ／ `found=true`
★(3) ★口 = 同上 ／ ★欄 = `sent.text` ／ ★id = 同上
     ★読める物 = ★★"半角英字" の語（★v1.18＝この版の変更が 届いたことの確認）
★(4) ★sha256 一致 ／ ★(5) ★戻せる ／ ★(6) ★61本を走らせない ／ ★(7) ★commit しない
```

## 5. ★★私が 言っていないこと

```
★『これで 全部の返答が 読める』―― ★★標本は 3件で、★★3件とも PASS です。
   ★★FAIL の 実データは ★1件も 在りません ∴ ★FAIL の枝は ★観測ではなく ★作りです。
   ★★★戻す条件 = ★実際に FAIL が 返った時に ★その1件を fixture に 足す。
★『13件が 通る』―― ★何も 予告していません。
★『初稿が 間違っていた』―― ★★初稿は ★実データの前に 書かれた物です。
   ★★変わったのは ★★材料が 増えたことです。
```
