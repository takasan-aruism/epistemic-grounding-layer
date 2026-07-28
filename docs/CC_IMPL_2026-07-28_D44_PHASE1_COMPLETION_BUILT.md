# 実装 → 設計/監査: **`DS → RRI → EGL` が同一 run で追跡できました**（Taka ②の合否条件を満たしました）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-28 / TYPE=BUILT
- **運用方針 確認済（版: v2.7 — `§12` を最大版で読んだ値）**
- 実装源: `CC_DESIGN_2026-07-28_D44_PHASE1_COMPLETION_BUILD_SPEC_v1_0.md` v1.0
- **受領した文書**: 上記 / `CC_DESIGN_2026-07-28_D44_HANDOFF_TO_IMPL.md`

## 到達経路
- [x] **(A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て届いた。

## 結果（★2軸）
### 経路
- [x] **実装した**（合流点⑤ ＋ 契約表1行）
### 実測
- [x] **★受入②（合否）: `component` に `EGL` が現れた。** **`SUBMIT → DS → RRI → EGL` が同一 run で1本に繋がった**
- [x] 受入① `core.append_event` に emit を置いた差分＋契約表の1行
- [x] 受入③ **`head` / `limit` / `-m` / `tail` を1つも使っていない**（コマンドを掲載）
- [x] 受入④ 各走査に「総N件 / 確認N件 / 打ち切り無し」を記載
- [x] 受入⑤ **独立に再走査し、設計の計数と★一致した**
- [x] 追加 既存の読み手が不変（sha256 一致）＋ 非回帰が基準と同一

---

## 1. ★受入②（本 build の合否）— 実データ
```
再現: cd /home/takasan && python3 -m twoder.submit "<事前記録の文面・1文字も変えず>"
  → ★ETRACE_RUN_ID = ETR-f0fe8461c407 / RRI_REQUEST_TYPE = OBSERVE_CURRENT_STATE / exit=0

再現: GET /api/resolve?id=ETR-f0fe8461c407
  resolved=True / count=21 / truncated=False / total=21
```
**★全 event（21件すべて。打ち切っていません）**
```
ETR-f0fe8461c407-0001  SUBMIT  ENTRY         parent=None
ETR-f0fe8461c407-0002  DS      UTTERANCE     parent=…-0001
ETR-f0fe8461c407-0003  RRI     mint          parent=…-0002
ETR-f0fe8461c407-0004  EGL     append_event  parent=…-0003
ETR-f0fe8461c407-0005  EGL     append_event  parent=…-0004
ETR-f0fe8461c407-0006  EGL     append_event  parent=…-0005
ETR-f0fe8461c407-0007  EGL     append_event  parent=…-0006
ETR-f0fe8461c407-0008  EGL     append_event  parent=…-0007
ETR-f0fe8461c407-0009  EGL     append_event  parent=…-0008
ETR-f0fe8461c407-0010  EGL     append_event  parent=…-0009
ETR-f0fe8461c407-0011  EGL     append_event  parent=…-0010
ETR-f0fe8461c407-0012  EGL     append_event  parent=…-0011
ETR-f0fe8461c407-0013  EGL     append_event  parent=…-0012
ETR-f0fe8461c407-0014  EGL     append_event  parent=…-0013
ETR-f0fe8461c407-0015  EGL     append_event  parent=…-0014
ETR-f0fe8461c407-0016  EGL     append_event  parent=…-0015
ETR-f0fe8461c407-0017  EGL     append_event  parent=…-0016
ETR-f0fe8461c407-0018  EGL     append_event  parent=…-0017
ETR-f0fe8461c407-0019  EGL     append_event  parent=…-0018
ETR-f0fe8461c407-0020  EGL     append_event  parent=…-0019
ETR-f0fe8461c407-0021  EGL     append_event  parent=…-0020

component の内訳: {'SUBMIT': 1, 'DS': 1, 'RRI': 1, 'EGL': 18}
★EGL が現れた: True
親子: root=1 / root から辿れた長さ=21 / 全 event=21 → ★1本に繋がった（孤立0件）
```
- **★台帳を直読していません。** **2DER に id を渡して聞いた結果です。**
- **前回（D-43）は3件で EGL が現れませんでした。** **今回18件現れています。**

## 2. 受入① 実装（合流点⑤）
```diff
（egl/egl/core.py::append_event — events.jsonl への append の直後・★_idlock を出てから）
+    try:
+        from ds import etrace as _ET
+    except ImportError:
+        …（`ds` が中身の無い名前空間として束縛されている場合のみ解決し直す）
+    if _ET.emit("EGL", "append_event",
+                {"event_type": event_type, "object_type": object_type, "new_prefix": new_prefix},
+                {"object_id": object_id}, "OK") is None:
+        raise RuntimeError(
+            "EGL append_event: Event Trace に書けなかったため中断した (fail-closed)")
     return object_id
```
```diff
（egl/egl/contracts.py — GUARD_CONTRACTS["core.append_event"].guarantees）
+            "Event Trace へ emit する(fail-closed)。書けなければ RuntimeError で中断する"
+            "(合流点⑤ / Taka 裁定「記録失敗時は fail-closed で」)。★_idlock の外で emit するので"
+            "ロック保持時間は延びない",
```
- **★`_idlock()` の中に入れていません**（`H6: 並行採番の直列化` を壊さないため）。
- **引数・返り値・保存内容を1つも変えていません。** **EGL の object graph に何も足していません。**
- **⑤専用の形を作っていません**（①〜④と同じ `emit` 呼び出しです）。
- **例外メッセージに「Event Trace に書けなかったため中断した」と明記しました**（黙って別の例外に見せない）。

## 3. ★受入⑤ 独立の再走査（過去を1つも流用していません）

### 3-1. 全書き込み経路（★総件数を先に出しました）
```
再現（★head / limit / -m / tail を1つも使っていません）:
  grep -rEn "open\([^)]*[\"'](a|w)[\"']|\.write_text\(|\.open\([\"'](a|w)[\"']\)" --include=*.py <repo> \
    | grep -v "test_\|/regression/\|/experiments/\|run_.*benchmark"
  （egl のみ追加除外: demo_ / /structure/ / /docs/）

  ds/ds            2 件
  rri/rri          2 件
  egl（全体）      15 件
  dev-workcell（全体） 10 件
  ────────────────────
  ★合計 29 件 / 確認 29 件 / 打ち切り無し
```
> **★設計の計数（ds=2 / rri=2 / egl=15 / dw=10 / 計29）と★完全に一致しました。**
> **∴ 2つの独立な計数が一致した、と書けます。**

### 3-2. 入口（★総件数を先に出しました）
```
再現（同じく打ち切りなし）:
  grep -rn --include=*.py -F "<pattern>" ds rri egl dev-workcell twoder \
    | grep -v "def …\|test_\|/regression/\|/experiments/\|/structure/\|/probe/\|\.pyc"

  submit(            9 件
  create_task(      10 件
  record_utterance(  5 件
  ★合計 24 件 / 確認 24 件 / 打ち切り無し
```
- **★前回の「12入口」に合わせていません。** **今回は呼び出し箇所を関数別に数えたため、母数の定義が違います**（前回は「入口」単位、今回は「呼び出し行」単位）。**同じ数字にならないのは定義差であり、どちらかが誤りだとは書きません。**
- **★この差の解消は私の担当ではないと判断し、事実として両方を残します。**

## 4. 受入③④（打ち切りを使っていないこと）
- **本文書に貼ったすべての走査コマンドに `head` / `tail` / `limit` / `-m` が含まれていません**（上に逐語で掲載）。
- **event 列も21件を全数掲載しました**（`truncated=False` / `total=21`）。
- **各走査に総件数・確認件数・打ち切り無しを書きました。**

## 5. 既存が不変であること
```
/api/claude_packet  before 109f58874740 / after 109f58874740  ★一致
/api/state          before f1c971e61fbe / after f1c971e61fbe  ★一致
非回帰98本          91 passed / 7 failed（基準と★顔ぶれまで同一・diff 空）
```

### 5-1. EGL 自身のテスト（実装源 §6-4 の「落ちたら報告」）
```
再現: egl 配下の test_*.py を全数（23本）走らせた。★打ち切り無し。
結果: 20 passed / 3 failed
  1 egl/docs/test_status_views.py         … ModuleNotFoundError: No module named 'status_views'
  1 egl/docs/test_status_views_S0_2.py    … 同上
  1 egl/test_process_optimizer.py         … 12/14（§11 の2件）
```
**★3本とも私の変更が原因ではありません。**
```
再現: 私の変更（core.py / contracts.py）を一時退避して同じ試験を実行
  egl/test_process_optimizer.py → ★12/14（退避前と同じ）
  status_views.py はリポジトリに存在しない（∴ 私の変更と無関係）
  その後、退避を戻して差分が復元されていることを git diff --stat で確認済
```
**★「落ちなかった」と書かず、「落ちた3本は私の変更前から落ちている」と書きます。**

## 6. 守った禁止事項（実装源 §2-3）
- **`webui.py` を変えていません。endpoint を足していません。**
- **`ids.py` を変えていません。**
- **合流点①②③④の実装を1行も変えていません。**
- **`twoder` 自身の台帳9つに手を出していません**（`G-48`）。
- **進行経路の run／`_emit_pending` への emit を含めていません。**
- **`rthread_events` / `dw/authorization` を塞いでいません**（`G-45`）。
- **投入は1回だけ・文面は1文字も変えていません。** **`cd /home/takasan` を明示してから実行しました。**
- **commit していません。**

## 7. 予想と実際（実装源 §5-1）
| 項目 | 設計の予測 | **実際** | 判定 |
|---|---|---|---|
| **EGL の event が出るか** | **出る方に賭ける** | **★出た（18件）** | **当たり** |
| EGL の event が何件出るか | 予想しない | 18件 | — |
| `request_type` | 予想しない | `OBSERVE_CURRENT_STATE` | — |
| **親子が1本に繋がるか** | **繋がる方に賭ける** | **★繋がった（21/21・孤立0）** | **当たり** |

## 8. 未確認（引き継ぎます）
1. **`DW_IMPLEMENTATION` 枝で `append_event` が走らないこと**は**確かめていません**（今回の依頼は取得系に入ったため、その枝を通っていません）。**実装源 §7-1 の宿題はそのまま残ります。**
2. **1回の取得系依頼で `append_event` が18回走ることが分かりました**（実装源 §7-2 の未確認に数で答えられます）。**ただし1回の観測です。**
3. **`pending_actor.jsonl`（`G-41`）は範囲外のまま未カバーです。**
4. **本 build に含めなかった宙に浮いた裁定2件**（`G-46` / **合流点④の fail-closed 化**）は、実装源 §3 のとおり**私も含めていません**。**★合流点④は現在も fail-open のままです。**

---
*IMPL BUILT（D-44 Phase 1 完了条件）。★合否条件（Taka ②）を満たした——CLI 1回投入（事前記録の文面を1文字も変えず・`cd /home/takasan` を明示）で `ETRACE_RUN_ID = ETR-f0fe8461c407` を得て `GET /api/resolve` で**21件すべて**を取得（`truncated=False`）、`component` の内訳は `SUBMIT:1 / DS:1 / RRI:1 / **EGL:18**` で **EGL が現れ**、親子は root 1つから21件すべてが**1本に繋がった（孤立0）**。前回 D-43 は3件で EGL が現れなかったので、その差が本 build の効果である。★実装=合流点⑤を `egl/egl/core.py::append_event` の append 直後・**`_idlock` を出てから**置き（H6 の直列化を壊さない）、fail-closed で書けなければ「Event Trace に書けなかったため中断した」と分かる `RuntimeError` を送出、⑤専用の形を作らず①〜④と同じ `emit`、引数/返り値/保存内容と object graph は1つも変えず、`egl/egl/contracts.py` の `GUARD_CONTRACTS["core.append_event"]` に契約1行を追加。★受入⑤=独立に再走査し、**設計の計数（ds=2/rri=2/egl=15/dw=10・計29）と完全一致**（2つの独立な計数が一致した）。入口は関数別の呼び出し行で数えて計24件だが、**前回の「12入口」とは母数の定義が違う**ので数を合わせず両方を事実として残す。★受入③④=貼ったすべての走査コマンドに `head`/`tail`/`limit`/`-m` を1つも使わず、各走査に総件数・確認件数・打ち切り無しを明記し、event 列も21件全数を掲載。既存は不変（`/api/claude_packet`・`/api/state` が sha256 一致、非回帰98本が基準 91/7 と顔ぶれまで同一）。★EGL 自身の試験23本は 20 passed / 3 failed だが、**私の変更を一時退避しても同じ結果**（`test_process_optimizer` は退避前後とも 12/14、`status_views.py` はリポジトリに存在しない）∴「落ちなかった」ではなく「落ちた3本は変更前から落ちている」と書く。禁止事項（webui/ids/①〜④/twoder 台帳/進行経路の run/`_emit_pending`/`G-45` の2件）はすべて守り、投入は1回・commit なし。予想は「EGL が出る」「親子が繋がる」の2つとも当たり、件数と `request_type` は予想しないと事前に書いた。★未確認=`DW_IMPLEMENTATION` 枝で `append_event` が走らないことは確かめていない（今回は取得系に入ったため）／1回の取得系依頼で `append_event` は18回走った（1回の観測）／`pending_actor.jsonl` は範囲外のまま／**宙に浮いた裁定2件（`G-46` と合流点④の fail-closed 化）は含めておらず、合流点④は現在も fail-open のままである**。*
