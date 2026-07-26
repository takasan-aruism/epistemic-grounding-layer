# CC 管理(MGR) → 設計/実装(CC-α): (a) retention 補修 GO（HANDOFF）

- `BUILD_ROLE: 参照`（実装源でない・下記スペックを名指すだけ）
- 宛: DESIGN/IMPL/AUDIT(CC-α) / 発: MGR / 2026-07-26 / TYPE=HANDOFF
- 権限: **Taka「(a) に GO。retention 補修を進めて」（2026-07-26）**。
- 対応: `CC_DESIGN_2026-07-26_BINDER_CONTEXT_ADJUDICATION_FINDING.md` §3 (a)

## GO：(a) 記録の規律を直す（機能追加でなく retention 補修）
承認済み (a) の中身:
1. **発話記録時に「直前発話 id」を書く**（同一 conversation_id の直前を `phase0.utterances()` から**決定論で**。新情報源なし）。
2. **実 ts を渡す**（配管は DE-0539 で既存）。**既定ハードコード値に落ちた事実も記録**（後から見分け可能に）。
3. **前向きのみ・過去は救えない**（隠さず明記）。

## 効果・規律
- これで **DS の「直前の文脈」が今後 populate** され、**P2 の束縛先チェックが実データで初めて測れる**。
- **却下済**: (b) 先に配線（正しさ検証手段なしで LIVE を触る＝規律の逆）／(c) P4 代替化（P4/1c は本命として独立進行・P2 は保留で放棄でない）。

## 進め方（BUILD_ROLE 規約）
- **DESIGN が (a) を 1 本の `★実装源` BUILD_SPEC に統合**（or 本裁定 §3(a) を実装源に指定）→ IMPL はそれ1本から作る。
- 各 BUILT → 監査独立再検証（**検証者名を明示**＝`【監査:CC-α】` 等・他人名の【監査】は再検証してから依拠）→ MGR/Taka。
- 不変: 前向きのみ明記・決定論・sole-writer・捏造ゼロ・commit=Taka・3 repo(rri/twoder/egl)は各 commit+push・★3 本線は止めない。
- P4（1c＝HBB-30 本体）は並行で本命として進行。
