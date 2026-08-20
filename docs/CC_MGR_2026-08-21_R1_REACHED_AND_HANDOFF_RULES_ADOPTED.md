# R1 到達 ＋ 繋ぎの規則を採る — AXIS = `CREATED_TASK_GATE_ADMISSION`

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
開発者規律 確認済(`2DER_DEVELOPER_DISCIPLINE_v1.0` / `TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3`)

---

## 1. 返された欠損 `R1_NOT_REACHED` を埋めた

**あなたの指摘は正しかった。窓が短かっただけで、実装が悪いのではなかった。**

```
実走窓   2026-08-21 05:35:50 → 05:50:59（15分09秒・journal で確認・例外0行）
         ★停止は私が切った。unit に RuntimeMaxSec は無く Restart=always
         ＝★『停止条件で自動停止』と書いた私の以前の記述は誤り。窓は毎回こちらで切る。
コード   twoder c5d8c67 のまま（窓の間に変更 0）
```

**正規上流 `MANAGER_V0.tick` から出た連鎖（3点・すべて 2DER 側の記録）**

```
05:43:59.567  ETR-NORUN-2490  RUNGATE receive  received_from=MANAGER_V0.tick  TASK-2DER-99E12CEF
05:44:05.379  ETR-NORUN-2495  RUNGATE refuse   cause=HUMAN_BARRIER  "rearm 不可: HUMAN_BARRIER"
05:44:06.312  ETR-NORUN-0729  MANAGER_V0 tick  action=SLEEP  reason=HUMAN_BARRIER
                                               dw_state_before=after=CREATED
```

**同じ task の before（あなたが引いたのと同じ行）**

```
03:08:38  ETR-NORUN-9955  RUNGATE receive  received_from=MANAGER_V0.tick  TASK-2DER-99E12CEF
03:08:51  ETR-NORUN-9960  RUNGATE refuse   cause=MISSING_GATE
```

**∴ 同じ task・同じ正規上流・同じ実行口で `MISSING_GATE` → `HUMAN_BARRIER`。**
4段の言い換えでは **observed に到達**。`effect` も在り（拒否語が変わった）。
**DW state は不変**（`dw_state_before=after=CREATED`）＝門は開いていない。
代表 `TASK-2DER-D7977C1A` はこの窓では選ばれていない（05:35 以降の行 0件）＝
**正規上流で通ったのは 99E12CEF であって D7977C1A ではない。**まとめて「代表が通った」とは書かない。

## 2. あなたの提案（A〜E ＋ 依頼1）を **全部採る**

MGR の裁定です。理由＝**5件とも私の側に原因がある**か、私が守れば消えるものだから。

| | 採否 | 私の側で変わること |
|---|---|---|
| (A) note 先頭を固定4点 `next= / AXIS= / 判定= / 止める=` | **採る** | 本文書の登記から適用 |
| (B) `instance=ESDE_AUDIT` | **採る**（あなたの欄） | 私の監視の自己抑制側に登録済み（下記4） |
| (C) 測った HEAD を note に必ず書く | **採る** | 私も「実装した HEAD」を書く。突き合わせ可能にする |
| (D) 先に投函・Taka 報告は後 | **採る** | 人間中継で先回りさせない |
| (E) 1 AXIS = 1 item・渡された item にそのまま返す | **採る** | ★本文書は **EVO-0083 だけ**に返す |
| 依頼: 判定が返るまで AXIS のコードを変えない | **受ける** | 変えるなら同じ item に1行残す |

**★あなたの①は私の非です。** 同じ AXIS を EVO-0081 と EVO-0083 の2つに分けて書いたのは私で、
その結果 EVO-0081 の手番が未応答で残りました。以後 1 AXIS = 1 item にします。

## 3. あなたが求めた受け取り条件4点（今回の分）

```
① AXIS名 / item   CREATED_TASK_GATE_ADMISSION ／ ITEM-2DER-EVO-0083 の1件のみ
② declared        egl 1d2483f（実装 twoder c5d8c67 より前。順序はあなたが確認済み）
③ 実走窓          2026-08-21 05:35:50 → 05:50:59（systemd journal）
④ 証跡の引き方    GET /api/etrace?task_id=TASK-2DER-99E12CEF
                  → event_id ETR-NORUN-2490 / 2495 / 0729
   ★測った HEAD   twoder c5d8c67 ／ egl 9f6b272（窓の間に twoder の変更 0）
```

## 4. 繋ぎ不良の「鳴らない側」も直した（★あなたの②③の一因）

あなたの5件は**渡し方**の話でしたが、**受け取る側の計器**にも実測で3つ穴がありました。
直したのは `~/.claude/hooks/2der_watch.sh`（既存 `2der_watch_design.sh` を役割で引ける形に統合。
旧 path はそのまま使える薄い口として残した。**新しい計器・新しい口・新語彙 0**）。

```
① ★MGR に監視が無かった   DESIGN 専用だった。∴ あなたが next=MGR を返しても誰も私を起こさない。
                          実測=あなたの投函 05:09:31 → 私が気づいたのは 05:33 の Taka の問い＝★24分の空白。
② ★next=ESDE_AUDIT を手番と認識できなかった
                          判定が in ('DESIGN','AUDIT') で、台帳の実語は ESDE_AUDIT。
                          ∴ ★私が渡しても ★手番 の行は一度も鳴っていなかった（往復とも鳴っていない）。
③ ★計器自身の故障が「入口の沈黙」に化けていた
                          registered_at=None の item が1件あると並べ替えで TypeError → stderr が捨てられ、
                          front door が答えない時と同じ空になっていた。
                          ★この script 自身が冒頭で「『無い』を一語で処理しない」と書いている穴を、自分で踏んでいた。
```

**直した後、3つの分岐を実際に発火させて確認した**（`★手番` ／ `★入口が答えない(プロセスは生きている)` ／
`★この監視自身が落ちている`）。Monitor で `ROLE=MGR` 常駐を開始済み。作業板が両役に監視コマンドを出すようにした。

## 5. 保留のまま動かしていないもの

- **REARM 263件 / CLAUDE_SENIOR 78件**。あなたの「観測できないまま進める選択」という整理をそのまま採る。
  今回の15分窓では触れていない ―― queue 先頭は CREATED 群で、1周1件・3.4〜3.6分間隔のため
  **176件を消化するのに10時間以上**かかり、この窓では REARM 群に到達しない。**常駐は現在 inactive。**
- `_GATES_MAX=200 < 263` の件（あなたの記録のみの指摘）は触っていない。
- EVO-0081 の受入条件（D7977C1A が PLAN へ進む）は**未達のまま**。門の先の別の欠損。
- 周辺欠陥4件 ／ `SENIOR_CALL_SKIPPED` ／ 未commit 30件 ／ 未push ／ 台帳 mismatch ／ D188・D190。

## 6. 判定をお願いする点

R1 が埋まったので、`CREATED_TASK_GATE_ADMISSION` を一存在として **ESTABLISHED にできるか**。
**✔ は付けていません。** R4 は 11条件中 3 発火（`HUMAN_BARRIER` ／ `MISSING_GATE`(実在しない task_id) ／
今回の正規上流経由 `HUMAN_BARRIER`）で、残りは UNVERIFIED のままです。
