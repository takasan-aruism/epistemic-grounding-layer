# 実装 → 設計/監査: Build 16 — **再起動は完了。⑥の手前で止めました**（同じ依頼文では `run_next` が `AUDIT` を撃つため）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-28 / TYPE=BUILT（**未完了・停止報告**）
- **運用方針 確認済（版: v1.9）**
- 実装源: `CC_DESIGN_2026-07-27_BUILD16_SPEC_RESTART_AND_GENERATE.md` v1.0
- **受領した文書**: 上記実装源 / `CC_DESIGN_2026-07-27_BUILD15_AUDIT_AND_RESTART_DIFF.md` / `CC_MGR_2026-07-27_BUILD15_AUDIT_RECEIVED_PROCEED.md`（写しで観測）
- **本文書は観測を書きます。判定・評価・提案の採否をしません。**

## 到達経路
- [x] **(A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て届いた。

## 前回からの持ち越し
- Build 15 の2ファイル: **MGR が commit 済**（状況表で `repo 未commit: なし` を観測）

---

## 0. ★結論を先に — ⑥を実行していません
**`TASK-2DER-21F64D9D` は現在 `READY_FOR_AUDIT` であり、`run_next` は `GENERATE` ではなく `AUDIT` を撃ちます。**
**実装源 §4-4「2段以上進めない（`AUDIT` へ行かない）」に当たるため、撃つ前に止めました。**
**∴ `/api/submit` も `/api/run_next` も実行していません。** **区分（5択）はいずれにも該当しないため、丸を付けていません。**

## 1. 再起動（常設手順・省略していません）
- **旧 pid / 旧起動時刻**: `1594748` / `2026-07-27 18:37:58`
- **ソース mtime**: `twoder/authority.py` `2026-07-27 23:24:27` / `twoder/generate_via_runner.py` `2026-07-27 23:24:27`
- **停止時刻**: `2026-07-27 23:56:53` 送出 → `23:56:55` 消滅確認（`kill 1594748`）
- **起動時刻 / 新 pid**: `2026-07-27 23:59:33` / `2746222`
- **使ったコマンドそのもの**:
```
nohup python3 -m twoder.webui 8770 > /home/takasan/webui_8770.log 2>&1 &
```
  （実装源 §1-② の既存手順。**新しい起動方法を作っていません。**）
- [x] **起動時刻（23:59:33） > ソース mtime（23:24:27）**
- **応答確認**: `GET /api/tasks` → 認証なし `HTTP 401` / Basic 認証あり **`HTTP 200`**
  ※`127.0.0.1` では `HTTP 000`。**bind が tailscale 面のみ（`100.107.6.119:8770`）という既存の設計どおり**で、異常ではありません（`ss -ltnp` で確認）。

### ④ 応答による修理の確認
- [ ] 素の task_id を確認
- [x] **手段が無く未実施（③のみ）**

**根拠（列挙）**: `webui.py` の受け口を機械列挙した結果、**任意コードを評価する経路はありません**。
```
再現: grep -n "u.path ==" twoder/webui.py
GET : / /command /api/tasks /api/state /api/claude_packet /api/roadmap /api/resolve /api/control /api/pending_approvals
POST: /api/approve /api/submit /api/run_next /api/ingest /api/operator/advance
```
**`/api/approve` は新プロセス内で `grant_approval` を通りますが、本番台帳に GRANT 行を書きます。** **実装源 §2 の「台帳に試験行を残さない」に反するため使っていません。** **実装源が許した「手段が無ければ③のみで進めてよい・無理に作らない」に従いました。**

## 2. 依頼文が Build 13/14 と同一であることの決定論的な証拠【監査:IMPL】
実装源 §1 の依頼文を機械抽出しました（`CC_DESIGN_2026-07-27_BUILD13_SPEC_WORKER_WITH_CONTRACT.md` の ```` フェンス内・37〜102 行）。
```
文字数 2411（末尾改行を含む）
sha256(本文のみ・末尾改行なし) = d75aae14a24ae5a9027048114551a1fa1fe89462de0b7f5c8c81706b993a29db
マーカー = SKELETON / END / IMMUTABLE_TESTS / END
task_id = "TASK-2DER-" + sha1(raw).hexdigest()[:8].upper()      （twoder/submit.py:405）
  末尾改行なし(2410字) → TASK-2DER-BFCC5B7B
  末尾改行あり(2411字) → ★TASK-2DER-21F64D9D  ＝ Build 13/14 と一致
```
**∴ 依頼文はバイト単位で Build 13/14 と同一です**（同一 id を再現したことが証拠）。**1文字も変えていません。**

## 3. ★停止事由（決定論・LLM を使っていません）
```
再現: cd /home/takasan/dev-workcell && python3 -c "
from dw import dispatch; print(dispatch.next_legal_operation('TASK-2DER-21F64D9D'))"
結果: state='READY_FOR_AUDIT', operation='AUDIT',
      actor_role='INDEPENDENT_AUDITOR', actor_id='QWEN_AUDITOR',
      input_ref='LATEST_DIFF+TEST_RESULT', claude_barrier=False
再現: grep -n "READY_FOR_AUDIT" dev-workcell/dw/dispatch.py
  30: "READY_FOR_IMPLEMENTATION": ("GENERATE", "CODING_WORKER", …)
  31: "READY_FOR_AUDIT":          ("AUDIT",    "INDEPENDENT_AUDITOR", …)
```
- **Build 14 で `GENERATE` が（失敗として）1件記録され、状態が `READY_FOR_IMPLEMENTATION` → `READY_FOR_AUDIT` へ進んでいます。**
- **`claude_barrier=False` なので、撃てば止まらず `AUDIT` が走ります。**
- **同じ依頼文は同じ task_id に落ちるため（§2）、再投入しても同じ task を指し、状態は戻りません。**

### 3-1. 私が確かめていないこと（事実として）
- **`/api/submit` を既存 task に対して撃ったとき、状態が戻るか否かを実測していません。** **撃つこと自体が⑥の実行に当たるため、確かめていません。**
- **Build 14 の記録上、再投入後の events は `CREATE / PROCESS_EVENT / PLAN / GENERATE` の4件のままで、`CREATE` が二重化していません。** **これは記録からの観測であって、今回の実測ではありません。**
- **`GENERATE` をやり直す手段が在るか否かを、私は調べていません**（原因調査・機構設計は私の担当ではないため）。

## 4. 予想と実際（実装源 §3・実行した範囲のみ）
| 項目 | 実装源の予想 | **実際** | 判定 |
|---|---|---|---|
| 再起動 | 成功する | **成功（新 pid 2746222・`HTTP 200`）** | **当たり** |
| ④ の `task_id` | 素（`PROBE-RESTART`） | **確認手段が無く未実施** | **判定不能** |
| `dispatched` 以降すべて | — | **未実行** | **判定不能** |

## 5. 守った禁止事項
- **`/api/submit` / `/api/run_next` をどちらも実行していません**（⑥の手前で停止）。
- **`AUDIT` へ行っていません。`run_until_barrier` を使っていません。token を迂回していません。**
- **本番コードを1行も変更していません。**
- **`B9B4DA3B` / `D6A93450` に触っていません。**
- **受入オラクルを開封していません**（場所も見ていません）。
- **`twoder/runs/*.trace.json` を読んでいません。**
- **台帳に試験行を書いていません**（`/api/approve` を使わなかった理由が §1）。
- **保全ディレクトリを作っていません・上書きしていません。**
- **依頼文を1文字も変えていません**（§2）。

## 6. commit
**していません**（MGR）。**本 build で本番ファイルの変更はありません。**

---
*IMPL BUILT（Build 16・**未完了・⑥の手前で停止**）。再起動は常設手順どおり完了（旧 1594748/18:37:58 → 停止 23:56:53〜55 → `nohup python3 -m twoder.webui 8770` で新 pid 2746222/23:59:33、起動 > ソース mtime 23:24:27、Basic 認証で `HTTP 200`。`127.0.0.1` が `HTTP 000` なのは bind が tailscale 面のみという既存設計）。★④は webui の受け口を機械列挙した結果、任意コードを評価する経路が無く未実施（`/api/approve` は本番台帳に GRANT 行を書くため使わず、実装源が許した「無理に作らない」に従った）。依頼文は機械抽出し、2411字が `TASK-2DER-21F64D9D` を再現することでバイト同一を証明。★停止事由=当該 task は現在 `READY_FOR_AUDIT` で `next_legal_operation` は `AUDIT`（`claude_barrier=False`＝撃てば止まらない）。Build 14 で `GENERATE` が失敗として1件記録され状態が進んでおり、同じ依頼文は同じ task_id に落ちるため再投入しても状態は戻らない ∴ 実装源 §4-4「AUDIT へ行かない」に当たるので `/api/submit` も `/api/run_next` も実行していない。区分5択はいずれにも該当しないため丸を付けていない。未確認=既存 task への再投入で状態が戻るかは撃っていないので不明／`GENERATE` をやり直す手段の有無は調べていない（担当外）。*
