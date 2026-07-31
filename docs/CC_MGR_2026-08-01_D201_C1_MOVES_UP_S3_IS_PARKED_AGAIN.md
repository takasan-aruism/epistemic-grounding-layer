# 【D-201】★C-1（進捗の書き込み口）を★繰り上げて ACTIVE にする ／ ★S-3 は再び判定待ちで停止

- `BUILD_ROLE: 参照` / **宛: 設計/監査** / 写: Taka / IMPL / 発: MGR / 2026-08-01 00:4x / TYPE=STATUS
- **開発者規律 確認済（版: v1.0）** ／ **受領**: `CC_DESIGN_2026-08-01_D200_DISPOSITION_DRAFT_FOR_S3.md`（承認して ingest 済）
- **この .md がまだ .md である理由**: 裁定を台帳へ渡す口が無いため（★C-1。★本書で ACTIVE になる）

## 1. ★Taka 指摘（逐語）— **★採る**
```
★「★ledgerの更新が行われてないと ★モニター漏れするんかな。
   ★こっちに関しては ★少し優先度高めないと ★開発が途中で止まるんじゃないかな」
★★★そのとおりである。★実測で裏が取れる:
   ★front door の全体像は ★`roadmap-last-write 2026-07-22` を出し続けている。
   ★MGR の Monitor は ★DE / CHG は拾うが、★ITEM の進捗は ★1件も動かない（★書き手が無いため）
   ∴ ★★「どこまで進んだか」は ★機械から取れない。★取れるのは「何かが起きた」だけである。
```

## 2. ★裁定：★C-1 を ACTIVE にする
```
★S-3 は ★`JUDGE_REQUIRED` / `next_operation: BLOCKED` ＝ ★機械では進められない（★判定の手番）。
★★v0.3 §3.1 は ★BLOCKED を ★次の案件へ移ってよい状態としている ∴ ★ACTIVE を差し替える。
★★★C-1 = ★`POST /api/submit`（front door）↔ ★`roadmap_registry.set_status` の ★1本を繋ぐ。
   ★関数を新しく作らない ／ ★新しい台帳を作らない ／ ★主体欄（v0.3 §13.2）を必須項目にする。
★★★★廃止するもの（★同時に書く・規律9）: ①進捗を .md に書く運用 ②人が set する自己申告値。
★★★★★完了条件: ★front door から1件 書けた ／ ★その値が `/api/roadmap` で読める ／
   ★★.md を1本も増やさずに「いまどこか」が言える。
```

## 3. ★S-3 の走行記録（★実測。★誰が何をしたか）
```
★① 処置(DISPOSE): ★設計が案を書き、★MGR が承認し、★`POST /api/ingest` で戻した（★.md ではない）
   → ★state: `DISPOSITION_REQUIRED` → ★`READY_FOR_REGENERATE`（★設計の予告どおり。★外れていない）
★② ★`run_next` が ★refused（★run gate が閉じていた）
   → ★再投入 ★1回（★理由: gate の開け直し）。★依頼文は ★1文字も変えていない
   → ★★決定論で確認: ★`sha1(goal)[:8] = b37727e3` ＝ ★task_id と一致 ∴ ★新しい task は立たない
   → ★実際に ★同じ `TASK-2DER-B37727E3` が返った
★③ ★REGENERATE 実行（★actor: `QWEN_LIVECODER` / `CODING_WORKER`）→ `READY_FOR_AUDIT`
★④ ★AUDIT 実行（★actor: `QWEN_AUDITOR`）→ ★`JUDGE_REQUIRED` / `BLOCKED`
★★Claude がしたこと: ★処置1件・再投入1回・押下2回。★★中身は1文字も書いていない
★★★2DER がしたこと: ★再生成・監査。★`claude_packet` の `admitted_claims` に
   逐語「★The `render` function is implemented as a pure function …」＝ ★実装の主張が★立っている
★★★★ただし ★合否は ★まだ出ていない ∴ ★「荷物を積んだ」とは ★まだ書かない。
```

## 4. ★S-3 は誰の手番か（★止めない・順序だけ変える）
```
★`JUDGE_REQUIRED` ＝ ★上級の判定。★設計/監査が動ける時に ★処置と同じ形（`/api/ingest`）で戻す。
★★2周目の `JUDGE_REQUIRED` は ★rework 2回超の★強制昇格（`workcell.py:41`）＝ ★設計どおりの動作である。
★★★∴ ★これは ★詰まりではなく ★仕様。★C-1 を進めながら ★判定を待つ。
```

## 5. ★順序（★更新。★後回しにしたものを全部 書く）
| # | 件 | 扱い |
|---|---|---|
| **ACTIVE** | **C-1 進捗の書き込み口（submit ↔ set_status の1本）** | **★本裁定で繰り上げ** |
| 判定待ち | S-3 = `TASK-2DER-B37727E3`（`JUDGE_REQUIRED`） | 設計/監査の手番 |
| 次 | (2) 停止時に `next_information_need` を上書き | 予約 |
| その次 | (1) 契約 None を task 分岐で止める ／ C-2 申請書を 2DER 自身が作る | 予約 |
| **後回し** | `D-199` 単発 Claude 呼び出し ／ C-3 外の道を塞ぐ ／ `D-191` gate の意図 | **後回し** |

---
**決めたこと**: **①Taka の指摘を採る——進捗が台帳に書かれないので Monitor は「何かが起きた」しか拾えず、「どこまで進んだか」は機械から取れない。front door は今も `roadmap-last-write 2026-07-22` を出し続けている ②∴ C-1 を繰り上げて ACTIVE にする。S-3 は `JUDGE_REQUIRED`/`BLOCKED` で機械では進められず、v0.3 §3.1 が差し替えを許す ③C-1 は submit ↔ `set_status` の1本を繋ぐだけ。新しい関数も台帳も作らず、主体欄を必須項目にし、廃止するもの（.md 進捗運用・自己申告値）を同時に書く ④S-3 の走行——処置を `/api/ingest` で戻して `READY_FOR_REGENERATE` へ（設計の予告どおり）、`run_next` が refused だったので同一依頼文を1回 再投入（sha1 一致を先に確認したので新 task は立たない）、REGENERATE と AUDIT が 2DER のアクターで動き、再び `JUDGE_REQUIRED` ⑤Claude は処置1件・再投入1回・押下2回で、中身は1文字も書いていない。実装の主張は立ったが合否は出ていないので「荷物を積んだ」とは書かない ⑥2周目の `JUDGE_REQUIRED` は rework 2回超の強制昇格＝設計どおりで、詰まりではない ⑦後回しは D-199・C-3・D-191 の3件。**
