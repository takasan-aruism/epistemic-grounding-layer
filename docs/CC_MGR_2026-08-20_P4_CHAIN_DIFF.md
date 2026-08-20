# 第四 ―― 因果鎖の **差分宣言**（★変更後に どの点が 変わるか だけ ／ ★実装 0）

**2026-08-20 19:3x ／ ★Taka 裁定 §7 ／ ★実装主体＝2DER ／ ★Claude はコードを書かない**
**★元の 因果鎖 = `CC_MGR_2026-08-20_P4_CAUSAL_CHAIN.md`（18点×6問）。★以下は ★変わる点だけ。**

---

## 1. ★変わる点（★4点 ―― ★それ以外の 14点は 不変）

| # | 点 | **変更前** | **変更後（★裁定どおり）** |
|---|---|---|---|
| **7** | **PLAN schema** | `_plan_prompt` の 鍵に `linkage` が 無い | ★`linkage` を **正式 schema に 加える**（★Qwen が 書く 鍵に する） |
| **8** | **PLAN validate** | `STRUCTURED_KEYS` / `EXECUTABLE_KEYS` に `linkage` が 無い ∴ 欠けても 通る | ★`linkage` 欠落を **PLAN 受理時に fail-closed**（★既存の `{"recorded": False, "stage": "validation", "reason": [...]}` と 同じ 形） |
| **10** | **linkage declared** | **★誰も 作らない**（本線に 生成者が 居ない） | ★**`build_planner` が 生成主体**。★`record_plan` で 保存し ★後段は **同じ値だけ 読む**（★再生成しない） |
| **17** | **completion_blockers** | `JUDGE_REQUIRED` で 早期 return ∴ 到達しない ／ `linkage=None` で 素通り | ★`JUDGE_REQUIRED` では **linkage gate を 評価しない**（★既存 escalation の 責務）／ ★COMPLETE 時に **declared と observed を 比較** |

## 2. ★変わらない点（★14点 ―― ★念のため 明示）

```
1 USER REQUEST ／ 2 RRI分類 ／ 3 RRI門 ／ 4 RRI戦略 ／ 5 HANDOFF CONTRACT ／ 6 CREATE ／
9 PLAN recorded（★保存先は そのまま `{"implementation_packet": …}`）／ 11 GENERATE ／
12 observed edges ／ 13 AUDIT ／ 14 DISPOSE ／ 15 UPPER_REVIEW ／ 16 JUDGE_REQUIRED ／ 18 PROPOSE_COMPLETE
★★＝ ★新しい 点を 1つも 足さない。★新 state 0 ／ 新台帳 0 ／ 新 authority 0。
```

## 3. ★裁定の 反映（★逐語 → どの点に 効くか）

```
①linkage 生成主体は build_planner ／ Claude ingest では 生成しない → ★#10（★`webui:674` は 触らない）
②PLAN の 正式 schema に linkage を 加える                        → ★#7
③新規 IMPLEMENT では linkage 欠落を PLAN 受理時に fail-closed     → ★#8
④Qwen が 生成した linkage を record_plan で 保存し 後段は 同じ値だけ 読む → ★#9→#17（★再生成 禁止）
⑤completion 時に declared/observed を 比較                        → ★#17
⑥JUDGE_REQUIRED では linkage gate を 評価しない                   → ★#17（★既存 escalation の 責務）
```

## 4. ★実装後に 再実走して 照合する もの（★裁定 §8）

```
★同じ 18点×6問を ★もう一度 実走で 埋める。
★とくに ★変わる 4点は ★declared と observed を 突き合わせる:
   #7  Qwen の PLAN に `linkage` が 出るか（★実物の PLAN payload を 見る）
   #8  `linkage` を 欠いた PLAN が ★`recorded=False` で 止まるか
   #10 `record_plan` に 保存された `linkage` が ★後段で そのまま 読めるか（★再生成 0）
   #17 COMPLETE 時に ★declared/observed の 比較が ★実際に 走るか
★★1点でも「誰が作る／誰が読む／本線で呼ばれる」が 未確認なら ★COMPLETE に しない（★裁定 §9）。
```

## 5. ★していないこと

```
★実装 0 ／ コード 0行 ／ repo 変更 0 ／ 新 task 0
★`webui:674`（Claude ingest）に ★1文字も 触らない ＝ ★主体移管に 逆行しない
★SELF_DEV_TOKEN = ★5/5
```
