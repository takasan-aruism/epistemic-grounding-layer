# 設計/監査 → 実装: RTHREAD stage 1 v0.1a 修正 handoff（F-1 保存則 load-bearing 化）

- 発: 設計/監査（CC-α）/ 2026-07-24 / 対応監査: `CC_AUDIT_2026-07-24_RTHREAD_STAGE1_IMPL_CONSISTENCY.md`
- 変更範囲: `rri/rri/request_thread.py` の **`project()` FILL 本体のみ** ＋ `test_request_thread_stage1.py` に **T14c 追加**。
- 骨格署名・定数・例外・他10関数は**無改変**（byte 一致契約を維持）。

## §1. project() 修正指示（in_flight を独立導出へ）
`in_flight_count` を **残差(plug)でなく独立導出**する。他フィールドは現状維持。

- `disposed_qids = { e["question_id"] for e in QUESTION_DISPOSED }`（重複は集合で吸収）
- `in_flight_count = len([ q.question_id for q in QUESTION_RAISED if q.question_id not in disposed_qids ])`
- `resolved/open_gap/rejected/merged` は従来どおり **QUESTION_DISPOSED イベントの件数**（event count のまま）。

これで I1 `raised == resolved+open_gap+rejected+merged+in_flight` が load-bearing になる:
- 二重処分: raised=1, Σ処分=2, in_flight=0 → `1 != 2+0` → **HALT** ✓
- 幻処分: raised=1, Σ処分=1, in_flight=1（実問いは未処分）→ `1 != 1+1` → **HALT** ✓

> docstring 該当行を「`in_flight_count`=raise した問いのうち QUESTION_DISPOSED を1件も持たない question_id の数（残差でなく独立導出）」へ更新（設計側で確定済み文言・実装は本体をこれに合わせる）。`check_conservation` は無改変で load-bearing になる。

## §2. 追加テスト T14c（発注側同梱・実装は触らない）
実イベント経路の二重処分で `check_conservation` が HALT することを検査（dict 手改変でなく `_append` sole writer 経由）。

```python
# ── T14c (load-bearing) 実経路の二重処分は保存則で HALT する ────────────────
def test_t14c_double_disposal_halts_via_event_path(rt):
    tid = rt.open_thread("DS-5", "T")
    q1 = rt.raise_question(tid, "q1", "T", account_id="DEFAULT")
    rt.dispose_question(tid, q1, "RESOLVED", "T")
    # 同一問いを2度目の処分（sole writer 経由で実イベントを注入）
    rt._append({"type": "QUESTION_DISPOSED", "thread_id": tid, "question_id": q1,
                "disposal": "OPEN_GAP", "reason_code": None, "target_id": None,
                "ts": "T", "sealed_by": "rri.request_thread"})
    with pytest.raises(rt.RThreadConservationError):
        rt.check_conservation(rt.project(tid))
```

## §3. 受入
- 既存 4 テスト + T14c = **5/5 green**。
- 監査ハーネス `python /home/takasan/egl/docs/audit_rthread_stage1.py` が **VERDICT: CONSISTENT**（C. load-bearing = PASS）。
- 骨格 byte 一致（project 署名・docstring 以外の定数/例外/他関数は無改変）。

## §4. 完了後
- `CC_IMPL_2026-07-24_RTHREAD_STAGE1_v0.1a_BUILT.md` を置く → 設計側が再監査 → CONSISTENT なら commit=Taka。
- 解決時に DE 起票（live submit 経由、`twoder.submit` 開発エビデンス登録マーカー付き）。**手で ledger に書かない**。
