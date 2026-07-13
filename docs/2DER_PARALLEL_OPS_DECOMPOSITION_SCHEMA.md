# ITEM-2DER-PARALLEL-OPS-DECOMPOSITION — 成果物 schema

分解専用 ITEM の成果物 = 「子 ITEM 候補一覧」。子 ITEM の**正式 ID は監査・人間承認後**に発行する（本 schema は候補記述のみ、ID 発行はしない）。仕様書 §5 の候補 + §2/§13 の監査基準に対応。

## CHILD_ITEM_CANDIDATE schema (1 候補 = 1 レコード)
```
{
  "candidate_name": "",            // 例 PARALLEL-ROUTER (仮称、正式ITEM IDは未発行)
  "spec_section_refs": [],         // 親仕様のどの節に由来するか (例 ["4","7"])
  "scope": "",                     // この子ITEMが実装する範囲 (1つの責務)
  "deliverable": "",               // 具体的成果物 (module/schema/test)
  "depends_on": [],                // 他候補名への依存 (循環禁止)
  "role_layer": "",                // DS / RRI-RESEARCH / RRI-PLAN / RRI-PLAN-AUDIT / DW / JUDGE / PYTHON / EGL のどれを実装するか
  "acceptance_criteria": [],       // AC- に対応する検証項目 (schema/state/isolation/evidence)
  "rollback": "",                  // 実装失敗時の戻し方
  "migration_impact": "",          // 既存 submit/dispatch/operator/de_admission への影響
  "risk": "",                      // 主リスク (:8005使用? 承認要? 破壊的?)
  "requires_live": false,          // live/GPU/:8005 を伴うか
  "authority": "",                 // AUTO_EXECUTE / REQUIRES_APPROVAL
  "hermetic_testable": true        // hermetic に受入試験できるか
}
```

## DECOMPOSITION_OUTPUT schema (分解 ITEM 全体の成果物)
```
{
  "parent_item_id": "ITEM-2DER-PARALLEL-OPS",
  "parent_artifact_id": "",        // 親仕様書 artifact
  "decomposition_item_id": "ITEM-2DER-PARALLEL-OPS-DECOMPOSITION",
  "proposals": [],                 // 最低3案 (§12 Phase2: 複数独立workerによる分解案)
  "audit": {                       // 別workerによる監査 (§12 Phase2)
     "gaps": [], "overlaps": [], "dependency_cycles": [], "granularity_issues": [],
     "missing_acceptance": [], "missing_rollback": [], "migration_conflicts": []
  },
  "recommended_candidate_set": [], // 監査後の推奨子ITEM候補 (CHILD_ITEM_CANDIDATE[])
  "sequencing": [],                // 実装順 (§12 Phase3-7)
  "open_questions": [],            // 人間承認が要る論点
  "child_ids_issued": false        // 正式子ITEM ID は承認後 -> ここでは常に false
}
```

## 規律（この分解 ITEM 自体に適用）
- **正式子 ITEM ID は発行しない**（分解案の監査・人間承認後）。候補は candidate_name（仮称）のみ。
- 分解案は **最低3案 + 別 worker 監査**（§12 Phase2）。移行期は Claude 兼務を EGL 記録（§11, AC-14）。
- Claude Code は分解案を「自分で作り自分で承認」してはならない — 監査は別 context/別 artifact、最終承認は Taka。
- 想定候補（§5、仮称）: PARALLEL-ROUTER / ROLE-SCHEMA / RESEARCH-PACKET / PLAN-PACKET / ATOMIC-TASK-SCHEMA / EXECUTION-PACKET / PROCEDURE-AUDIT / JUDGE-PACKET / ESCALATION-PACKET / EGL-INTEGRATION / MODEL-ROUTING / MODEL-SELECTION-TEST / CONCURRENCY-BENCHMARK / ACCEPTANCE-HARNESS / MIGRATION。
