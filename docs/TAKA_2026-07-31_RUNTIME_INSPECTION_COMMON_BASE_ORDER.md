# Taka 指示（逐語・全文）— Runtime Inspection 共通基盤の形成

- **種別**: Taka 直接指示の正典（★逐語。★編集しない）
- **受領**: 2026-07-31 00:49 / **記録者**: MGR
- **裁定**: `CC_MGR_2026-07-31_D144_TASK_IS_THE_ONE_FIX.md`
- **直前の報告書**: `CC_MGR_2026-07-31_D143_TRIAL2_REPORT.md`（★変更しない）

---

## 目的

今回の目的は GPU機能を完成させることではない。

目的は、

**Runtime Inspection を 2DER の共通基盤として成立させること**

である。

---

## 評価対象

評価するのは能力ではない。

評価するのは配線である。

以下が一本の流れとして最後まで接続されること。

```
Request
↓
RRI
↓
Task生成
↓
Runtime Inspection
↓
Observation
↓
Ledger
↓
DW
↓
User Response
```

途中で一箇所でも切れていれば、その地点が今回の修正対象となる。

---

## 実施方針

GPU取得処理そのものを改善することは目的ではない。

GPUは Runtime Inspection を検証するためのサンプルケースとして扱う。

新しいアーキテクチャは作らない。

新しい帳票も作らない。

既存構造へ最小限の修正のみ行うこと。

---

## 修正ルール

一度に一箇所だけ修正すること。

修正後は必ず同じ検査を再実行すること。

途中で新しい改善案を実装し始めないこと。

設計変更は禁止。

能力追加は禁止。

今回確認したいのは

**「一本の道が最後まで通るか」**

だけである。

---

## 完了条件

GPU取得が成功することではない。

以下すべてが PASS になること。

```
Request        PASS
RRI            PASS
Task           PASS
Runtime        PASS
Observation    PASS
Ledger         PASS
DW             PASS
Response       PASS
```

途中で停止した場合は、

```
Last PASS :
First FAIL :
原因 :
修正内容 :
次回確認箇所 :
```

のみ報告すること。

---

## 共通基盤としての確認

今回最も重要なのは、

Runtime Inspection が GPU 専用ではなく、

```
Runtime Inspection
 ├── GPU
 ├── CPU
 ├── Memory
 ├── Disk
 ├── Process
 ├── Network
 └── ...
```

という形で今後そのまま利用できる共通入口になっているか確認することである。

GPU固有のコードを書くのではなく、

**Runtime Inspection という共通経路の形成を優先せよ。**

---

## 最終報告

最後に以下のみ簡潔に報告すること。

* 今回接続できた配線
* まだ切れている配線
* 次回修正すべき箇所（1件のみ）
* Runtime Inspection を他の監視項目へ再利用できる状態かどうか

---
*Taka 直接指示の正典（2026-07-31 00:49 受領）。★逐語。★裁定は `D-144` に書く。*
