# BUILD SPEC — Build 13: **契約を添えて投入し、PLAN まで1段進める**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源。**IMPL はこの1本だけから作る**）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.9）**
- 権限: `CC_MGR_2026-07-27_STAGE3_GO_RESUME_DEV.md`（Taka「開発を進めて」）

## 0. ★資料で確認した（MGR §1-4 の義務）
`2DER_EXECUTION_ARCHITECTURE.md` / `.json` の該当箇所:
- `C-CONTRACT-SEAL` = `LIVE`（`submit.py:430`・PLAN より前に封印）
- `C-BUILD-PLANNER` = `LIVE` / `C-QWEN-WORKER` = `LIVE`
- `G-01`（front door から台帳を読む経路が無い）＝ **本 build が作らせる対象**
- `SM-DW`: `CREATED → PLAN`（`claude_barrier=True`・機械上書きあり）

**★資料に無かったので実物を読んだ**（`generate_via_runner.py:77-99`）:
```
skeleton / immutable_tests は bytes 一致で渡る
target_file="impl.py" / test_file="test_impl.py" / test_body=immutable_tests
implementation=skeleton（★worker は「全文生成」。骨格を種に impl.py を丸ごと書く）
生成後に verify_skeleton_preserved で骨格の固定区間を決定論検査
```
**∴ `skeleton` は「`impl.py` の骨格（署名＋docstring）」、`immutable_tests` は「そのまま `test_impl.py` になるテスト本文」である。**

## 0-1. これは何か
| | |
|---|---|
| **これは** | **契約付きの依頼を投入し、`PLAN` まで1段だけ進める** |
| **これではない** | **GENERATE しない**（次の build）。**検査・配置・配線もしない** |
| **Build 12 との違い** | **契約マーカーを付けた。** Build 12 の失敗は「2DER が作れない」ではなく「我々が契約を渡さなかった」 |

---

## 1. 投入する依頼文（**DESIGN が確定。IMPL は1文字も変えない**）

````
宛: 設計/監査(CC-α)
台帳IDの問い合わせに4状態で答える薄いアダプタを作ってほしい。production repo は触らないこと。
配置は依頼者が行う。標準ライブラリのみ。ネットワークを使わない。ファイルに書かない。
外部モジュールを import しないこと（resolve_fn は呼び出し側が渡す）。

<<<2DER:SKELETON>>>
def answer(rid, resolve_fn, known_prefixes):
    """台帳IDの問い合わせに4状態で答える。

    契約:
      - rid の接頭辞（"-" より前）が known_prefixes に無い -> {"state": "NOT_ANSWERABLE"}
        このとき resolve_fn を呼んではならない。存在しないと分かっているものを問い合わせない。
      - 接頭辞が在り resolve_fn(rid) が None 以外を返した -> {"state": "ANSWERED", "record": その返り値}
      - 接頭辞が在り resolve_fn(rid) が None を返した     -> {"state": "NOT_FOUND"}
      - resolve_fn が例外を投げた                          -> {"state": "UNKNOWN"}（例外を素通しさせない）
      - NOT_ANSWERABLE / NOT_FOUND / UNKNOWN は互いに別の値であること。
        NOT_ANSWERABLE=持ち主が無い、NOT_FOUND=探して無い、UNKNOWN=探せなかった。
      - 該当しないとき別の結果へ切り替えない。
    """
<<<2DER:END>>>

<<<2DER:IMMUTABLE_TESTS>>>
from impl import answer

KP = ("DE", "UTT")
_F = []


def _ck(name, cond, got=None):
    _F.append((name, bool(cond), got))


def _boom(rid):
    raise RuntimeError("boom")


def run():
    _ck("T1 未対応接頭辞 -> NOT_ANSWERABLE",
        answer("XYZ-0001", lambda r: None, KP).get("state") == "NOT_ANSWERABLE")
    rec = {"design_evidence_id": "DE-0525"}
    r = answer("DE-0525", lambda r: rec, KP)
    _ck("T2a 記録あり -> ANSWERED", r.get("state") == "ANSWERED", r)
    _ck("T2b record は resolve_fn の返り値そのもの", r.get("record") == rec, r.get("record"))
    _ck("T3 記録なし -> NOT_FOUND",
        answer("DE-99999", lambda r: None, KP).get("state") == "NOT_FOUND")
    a = answer("XYZ-0001", lambda r: None, KP).get("state")
    b = answer("DE-99999", lambda r: None, KP).get("state")
    _ck("T4 NOT_ANSWERABLE != NOT_FOUND", a != b, (a, b))
    calls = []
    answer("XYZ-0001", lambda r: calls.append(r), KP)
    _ck("T5 未対応接頭辞では resolve_fn を呼ばない", calls == [], len(calls))
    _ck("T6 falsy({}) だが None でない -> ANSWERED",
        answer("DE-0001", lambda r: {}, KP).get("state") == "ANSWERED")
    r9 = answer("DE-0001", _boom, KP)
    _ck("T7 例外 -> UNKNOWN", r9.get("state") == "UNKNOWN", r9)
    _ck("T8 UNKNOWN != NOT_FOUND", r9.get("state") != "NOT_FOUND", r9)
    bad = [(n, g) for n, ok, g in _F if not ok]
    for n, ok, g in _F:
        print(("PASS " if ok else "FAIL ") + n + ("" if ok else "  <- %r" % (g,)))
    print("%d/%d PASS" % (len(_F) - len(bad), len(_F)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(run())
<<<2DER:END>>>
````

**投入・進行（各1回）:**
```
POST /api/submit    {"raw": "<上記の全文>"}      → DW_TASK_ID を控える
POST /api/run_next  {"task_id": "<上で返った id>"}  → 1回だけ（PLAN）
```
- **`run_until_barrier` を使わない。** **PLAN が記録されたら止まる。GENERATE へ進まない。**
- **token を迂回しない。**

---

## 2. 予想を先に書く（実測前に固定）
| 項目 | DESIGN の予想 |
|---|---|
| `RRI_REQUEST_TYPE` | **`BUILD_CAPABILITY`** |
| `DW_TASK_ID` | **新しい id**（文面が変わったため） |
| **契約が封印されたか** | **★される**（マーカーを両方入れたため）。**確認は次段の `GENERATE` でしか出ない可能性がある** |
| PLAN の成否 | **成功する方に賭ける**（Build 11・12 とも PLAN は通った） |
| `planner_outcome` キー | **在る**（S3 が効いている） |

**★外れたら「外れた」と書く。**
**★特に `extract_contract` が `ValueError` を投げた場合**（マーカーの対応が壊れている）、**`/api/submit` が 500 か例外を返す。** **その場合は私の依頼文の欠陥である。** **そう記録して止めること。**

---

## 3. やってはいけないこと
1. **依頼文を1文字も変えない。** **マーカー行（`<<<2DER:...>>>`）を含めて。**
2. **GENERATE へ進まない。** **PLAN が記録されたら止まる。**
3. **`run_until_barrier` を使わない。**
4. **失敗しても手で書かない。** **`planner_outcome` / 例外を記録して上げる。**
5. **contract を新設・改変しない。**
6. **本番コードを変更しない。**
7. **受入オラクル（`sha256 77af566…`）を開封しない。** **★依頼文の `immutable_tests` は MUST の一部であり、オラクル全体ではない**（`[]` `""` `0` `False` の falsy 群と `known_prefixes` 空の検査は**held-out** として設計/監査が保持している）。
8. **トークンを文書・argv・ログに出さない。**

---

## 4. BUILT に置く定型見出し（そのまま）
```
## 到達経路
- [ ] (A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。
- [ ] (B) 〇〇（経路名）を経て届いた。

## プロセス鮮度（実行時）
- webui pid / 起動時刻:
- ソース mtime（webui.py / dispatch.py / submit.py / generate_via_runner.py）:
- [ ] 起動がソースより新しい / [ ] 古い（→ 止めた）

## 結果の区分（1つに丸）
- [ ] PLAN_RECORDED（PLAN が記録され READY_FOR_IMPLEMENTATION）
- [ ] PLANNER_REJECTED（planner_outcome に reason が出た）
- [ ] REFUSED（gate に拒否された）
- [ ] CONTRACT_MALFORMED（extract_contract が ValueError＝依頼文の欠陥）
```

## 5. そのほか出すもの
1. 投入した依頼文（逐語）と `/api/submit` の応答全文。
2. `/api/run_next` の応答全文（**`planner_outcome` の有無と中身を逐語**）。
3. `derive_state(<新 task>)` と events。
4. §2 の予想と実際の表。**外れに「外れた」と書く。**
5. **`TASK-2DER-B9B4DA3B` / `TASK-2DER-D6A93450` に触っていないこと。**
6. 各操作1回ずつ・本番無変更・**commit しない**・冒頭に「運用方針 確認済（版: v1.9）」。
7. **v1.5**: 「動く」と書くときは再現コマンドと結果を併記。

---

## 6. 位置づけ（緩めない）
- **PLAN が通っても「作れるようになった」と書かない。** **契約が封印されたかは、まだ分からない。**
- **1回の観測で常態を判定しない。**

---
*BUILD SPEC v1.0（★実装源）。Build 13=契約マーカー付きの依頼を投入し PLAN まで1段だけ進める（GENERATE は次の build）。★資料で確認したうえで、資料に無い契約の実物を読んだ——`skeleton`/`immutable_tests` は bytes 一致で渡り、`target_file=impl.py` / `test_file=test_impl.py` / `implementation=skeleton` で **worker は全文生成**、生成後に `verify_skeleton_preserved` で骨格の固定区間を決定論検査する。∴ skeleton は impl.py の骨格（署名＋docstring に契約を書く）、immutable_tests はそのまま test_impl.py になるテスト本文。依頼文は `<<<2DER:SKELETON>>>` と `<<<2DER:IMMUTABLE_TESTS>>>` を両方含み、テストは T1〜T8（4状態の分離・resolve_fn を呼ばない・falsy と None の区別・例外は UNKNOWN）。★immutable_tests は MUST の一部であり受入オラクル全体ではない（falsy 群と known_prefixes 空は held-out として設計/監査が保持）。予想=BUILD_CAPABILITY / 新 task / PLAN 成功 / `planner_outcome` キー在り。★`extract_contract` が ValueError なら私の依頼文の欠陥なのでそう記録して止める。禁止=1文字も変えない・GENERATE へ進まない・手で書かない・contract を新設しない・オラクルを開封しない・本番無変更。区分は PLAN_RECORDED / PLANNER_REJECTED / REFUSED / CONTRACT_MALFORMED の4択。PLAN が通っても「作れるようになった」と書かない。*
