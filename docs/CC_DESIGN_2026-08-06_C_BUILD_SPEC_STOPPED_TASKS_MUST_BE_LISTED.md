# 【BUILD SPEC】`C` — **★止まったことの通知：★口は 在る。★task 側だけが 載っていない**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-06 20:4x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.15）** ／ 台帳: `ITEM-2DER-EVO-0035`
- 元: Taka 指示 19:33 の **C**（★逐語『レビュー自体は人の手番のまま／★自動化するのは「止まったことの通知」のみ』）
- **★新台帳0 ／ ★新エンドポイント0 ／ ★核1（★純関数1つ）／ ★Claude の配線 ★上限6行**

---

## 1. ★★測ったこと（★front door の値・★逐語）

```
★`GET /api/pending_approvals` は ★★もう 動いている = ★★13件 を ★理由つきで 返す:
    {"task_id": "ITEM-2DER-EVO-0019", "item_status": "PLANNED",
     "title": "Independent audit layer …", "reason": "roadmap item marked REQUIRES_APPROVAL"}
★★★∴ ★『誰かの承認を待って 止まっている物』は ★★既に 機械が 答えている。

★★★★但し ★13件は ★すべて `ITEM-…` であり ★★`TASK-…` が ★1件も 無い。
★実測(★同じ front door):
    TASK-2DER-D28FF7E4 → ★state = ★★`JUDGE_REQUIRED`
    TASK-2DER-9A96D0D5 → ★state = ★★`READY_FOR_UPPER_REVIEW`
★★★★★∴ ★★上級レビュー／判定で 止まった task は ★どの一覧にも 出ない。
      ★★これが ★C で 足りない ★唯一の物である。
```

## 2. ★★私の非（★先に 書きます）

```
★★私は 本日 `EVO-0019` を ★『手番が 読めない』と 呼び、★MGR へ 上げ、★何時間も 待たせました。
★★★実測 = ★★2DER は ★最初から 答えていました（★`pending_approvals` に ★理由つきで 載っている）。
★★★★∴ ★私は ★2DER に 聞かずに ★自分の計器で 判断していた（★規律3 の 逆）。
★★★★★直し方 = ★『読めない』と 書く前に ★★同じことを 答える口が 無いかを 1回 引く。
```

## 3. ★★契約（★核・★純関数1つ）

**★依頼文**
```
task の状態から「人を待って止まっているか」を1語で返す純関数 impl.stop_reason_for_state を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
state = str
戻り値 = str または None。

読み方は4通り。上から順に、最初に当てはまった1つで決める。

(1) state が str でない → None
(2) state が "JUDGE_REQUIRED" → "AWAITING_JUDGE"
(3) state が "READY_FOR_UPPER_REVIEW" → "AWAITING_UPPER_REVIEW"
(4) (1)(2)(3) のどれにも当てはまらない → None

★大文字小文字は そろえない（文字ごとに 等しい時だけ 当てはまる）。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def stop_reason_for_state(state):
    # <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

**★封印試験（★7本）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

def test_judge_required_is_awaiting_judge():
    assert impl.stop_reason_for_state("JUDGE_REQUIRED") == "AWAITING_JUDGE"

def test_upper_review_is_awaiting_upper_review():
    assert impl.stop_reason_for_state("READY_FOR_UPPER_REVIEW") == "AWAITING_UPPER_REVIEW"

def test_running_state_is_none():
    """★止まっていない状態は None（★『止まった』と 言わない）"""
    assert impl.stop_reason_for_state("GENERATE") is None

def test_complete_is_none():
    assert impl.stop_reason_for_state("COMPLETE") is None

def test_case_is_compared_exactly():
    """★小文字は 別の語（★そろえると 別の状態が 混ざる）"""
    assert impl.stop_reason_for_state("judge_required") is None

def test_non_string_is_none():
    assert impl.stop_reason_for_state(None) is None

def test_empty_is_none():
    assert impl.stop_reason_for_state("") is None
<<<2DER:END>>>
```

## 4. ★★配線（★IMPL・★上限6行）

```
★`/api/pending_approvals` の 返す `pending` に、★task 側の 停止を ★同じ形で 足す:
    {"task_id": "<TASK-…>", "reason": "<AWAITING_JUDGE | AWAITING_UPPER_REVIEW>"}
★★理由の語を ★承認待ちと ★分ける（★Taka の A と 同じ考え方＝
   ★『見ていない』と『再現しない』を 別の値にする ＝ ★ここでは ★『承認待ち』と『レビュー待ち』を 分ける）。
★★★既存の13件は ★1件も 変えない（★`reason` も そのまま）。
```

## 5. ★★受入

```
★(1) ★`pending_approvals` に ★`TASK-2DER-D28FF7E4` が ★`AWAITING_JUDGE` で 出る
★(2) ★`TASK-2DER-9A96D0D5` が ★`AWAITING_UPPER_REVIEW` で 出る
★(3) ★★既存の13件(`ITEM-…`)が ★1件も 減らず ★`reason` も 変わらない
★(4) ★止まっていない task が ★★1件も 載らない（★陰性・★これが 無いと 一覧が 意味を失う）
★(5) ★Claude の配線行数を 逐語で 報告（★★上限6行。★範囲では 予告しません＝本日2回 外したため）
★(6) ★戻せる ／ ★(7) ★61本を走らせない ／ ★(8) ★commit しない ／ ★(9) ★twoder 配下で python を動かさない
```

## 6. ★★私が 言っていないこと

```
★『上級レビューを 自動化する』―― ★★していません。★載せるのは ★『止まった』という事実だけ。
★『Opus を 呼ぶ口を 作る』―― ★作りません（★Taka 逐語『開発中はいらん』）。
★『これで Claude の介入が 減る』―― ★★測るのは ★Taka が固定した指標（★上級レビューを除く介入回数）であり、
   ★本件は ★その分母を 見えるようにするだけです。
```
