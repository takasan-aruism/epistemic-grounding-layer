# Kickoff Decision Record — Walking Skeleton (Phase 1a)

日付: 2026-07-05
決定者: Taka(価値判断)/ Web Claude(設計整合確認)
宛先: Claude Code
位置づけ: 本書は設計書ではない。着手決定の記録である。

---

## 決定: (b) walking skeleton を先に貫通する

実RQ 1本を最小構成で最後まで通す:
```
RQ: 「NVFP4 は dual RTX5090 の持続 agent 負荷で安定か」
経路: Gap登録 → SearchPlan → Search Run → Observation → Fragment →
      Candidate Claim → Gate 0-3(code) → Gate 4(Claude) →
      Global受理 or EVIDENCE_INSUFFICIENT → Gap更新
```

このRQを選ぶ積極的理由: 持続負荷安定性は公式文書にまず書かれていないため、
綺麗な VERIFIED では終わらず、EVIDENCE_INSUFFICIENT / ABSENCE / gap残存 という
本システムの差別化機構そのものを初回から通行試験できる。
happy path だけの skeleton にならない。

component 一括分解は skeleton 貫通後、実際に書いたコードの境界から逆算して起こす。

---

## 着手決定 3件

### K-1 SoR = SQLite + jsonl event log(承認)
- jsonl = append-only event log(正本)。SQLite = current-state view。
- RC-3 整合: SQLite view は jsonl から常時再構築可能であること(受入試験対象)。
- vector index は不実装。1a の dedup は CS-1 フル走査で足りる。
- DD-6(storage は調査ベース選定)との関係: 本決定は bootstrap 用の
  可逆な足場(データ小・移行自明 = REPLAYABLE)であり、DD-6 の本選定を
  先取りしない。DE record として記録する(DE-0003)。

### K-2 Gate 4 adjudicator = Claude-in-loop(承認・既定通り)
- CB-1 のまま。benchmark B 完成までの teacher 運用。
- CB-5 を常時掲示: Claude findings は teacher signal であり ground truth ではない。

### K-3 Manager 境界の最小依存表(フラグD回答)
新テーブル不要。既存オブジェクトへの 1 フィールド追加 + 導出規則 1 本で足りる:
```
K3-1  CandidateClaim に resolves_gap: gap_id を追加する(候補がどの問いに
      答えるものかのリンク)。
K3-2  importance は保存せず導出する:
        gap.required_for が非空 → REQUIRED_FOR_RESOLUTION
        それ以外               → SUPPORTING
      (KGAP schema の required_for は v0.2 §9 で定義済み。
       requirements.json の REQ id は親文書 7.5 の Task Evidence 由来)
K3-3  DF-3/DF-4 の判定は上記導出値で行う。Manager 側に必要なのは
      requirements → gap の required_for 記入のみ(RD の要求分解時に記入)。
```
境界をまたぐ依存はこの resolves_gap 1 本に固定する。

---

## フラグ回答

### Flag A(設計が実装を追い越す)→ Amendment Moratorium 発動
```
MOR-1  以後の amendment は、Design Evidence Record の evidence class が
       OPERATIONAL(実運用 stream 由来)であるものを根拠とする場合のみ起こす。
MOR-2  armchair audit(私・GPT・Claude Code の設計上の指摘)は
       audit backlog に登録するのみとし、amendment 化しない。
       運用データが同じ欠陥を示した時点で backlog から起票する。
MOR-3  例外: skeleton 実装中に発見される「設計が実装不能・自己矛盾」の類は
       IMPLEMENTATION_BLOCKER として即時修正可(これは運用証拠の一種)。
MOR-4  DE-0002 の replication_status=SINGLE_AUDIT 系レコードは、
       operational 再現が取れた時点で REPLICATED へ昇格させる。
```

### Flag B(benchmark B が自律化の律速)→ マイルストーン明示
```
M-AUTONOMY: benchmark B(adjudicated 50〜100件)完成 + CB-3' 閾値通過 =
            local 35B Curator への移行判定が可能になる時点。
1a 開始には不要(K-2 の Claude-in-loop で走る)。
B の原料は operational stream から自然に溜まる(CB-2)ので、
skeleton を回すこと自体が M-AUTONOMY への前進になる。
```

### Flag C(この機材で「別重み」は高い)→ 独立性資源表
```
IR-1  独立性機構の選択はハードウェアトポロジの関数である。
      本環境の独立性資源とコスト:
        同一モデル別フレーム(別run/blind/別質問構造) … ほぼゼロコスト
        local model swap(Coder-Next ↔ Qwen3.6)      … 高(~4分・同時不可)
        API 別重み(Claude / GPT)                     … 低(金銭コストのみ)
IR-2  1a の FI-4 / EI-4 相当が必要になった場合、「別重み」は
      local swap ではなく API(Claude/GPT)で調達する。
      この機材における実質的な別重みは API である。
IR-3  local swap を要する独立性設計は 1a/1b では採用しない。
```

---

## DE 登録(K-1 と本決定)

```
DE-0003: {affected: SoR選定(足場), evidence: bootstrap必要性,
          replication: N/A(可逆足場), decision: PROVISIONAL_ADOPT,
          note: DD-6本選定はoperationalデータ後}
DE-0004: {affected: amendment工程, evidence: Flag A(設計4層・運用0),
          decision: AMEND(MOR-1〜4)}
```

以上。skeleton の骨組み開始を承認する。
