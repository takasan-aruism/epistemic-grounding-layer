# CC 管理(MGR) → 設計/監査(CC-α): front-door 移行(A) 分析＋第一スライス HANDOFF

- 宛: DESIGN/AUDIT(CC-α) / 発: MGR / 2026-07-26 / TYPE=HANDOFF
- 権限: Taka 承認（2026-07-26「合理的にそれならそれでいい」＝**A で進める**）。
- 位置づけ: 帳簿「見つける層」完成(DE-0537)→ **本来の問い合わせ(front door)に戻る**フェーズ。乱暴な全剥奪でなく**機能ごとに慎重に**移行。[[ai-must-be-internal-actor-not-intruder]]。

## 決定：A（front door 復帰）を優先順で
根拠: Claude 肩代わり9機能を実物棚卸し。**大半は"作ってあるのに迂回 or 意図的に切ってある"**。共通関所 `twoder/authority.py`(PRE_OP gate) が既存＝機能ごと独立移行が可能（接続容易・独立性高）。B(働く会計)は絡んで高工数＋front door 依存ゆえ後続。

**移行 優先順**（独立・低工数・高価値順）:
1. **DE 記録を submit 経由へ**（直叩き=公式 bypass をやめる）← **本スライス**
2. 開発作業を DW workcell 経由へ（迂回をやめ独立監査ゲートを効かせる）
3. instance間通信を確定（唯一の真の新規=#4）
4. ポリシーゲート(commit/自律駆動)は Taka が1つずつ意図的に開放
**残す(C)**: 判断/上級監査(SENIOR_REVIEW=到達点の役割)・自由調査・自由命名。

## 第一スライス（本 handoff の実作業）：DE 記録を submit 経由へ
**目的**: 我々の DE 記録を `de_admission` 直叩きでなく **submit の DE-admission fast path**(submit.py:107-147, DS→rri.admission_request.detect→egl.de_admission→residual_update) 経由にする＝「正面玄関から入る内部アクター」の最初の一歩。

**デリケート・ハンドリング（厳守）**:
- **並行運用でまず"同値"を証明**: submit 経由の admission が、直叩きと **byte 同値の ledger 行**を生むことを実証してから切替（差分が出たら surface・握り潰さない）。
- **直叩きパスは即座に塞がない**（この段では enforcement しない。証明→切替→（後の別スライスで）閉塞、の順）。
- submit.py:117-120 は NL のみだと boundary fail＝**構造化 admission_payload が要る**。我々の DE 記録に必要な payload schema を定義。
- 冪等・決定論・measure-first。sole-writer 分離不変・commit=Taka。★3 本線（帳簿）は止めない。

**依頼フロー**: DESIGN が最小スライス spec（submit-routed admission の payload schema・同値検証ハーネス・切替条件・不変テスト）→ IMPL 実装 → AUDIT 独立再監査 → 結果を MGR へ。切替可否の最終判断が要れば MGR 経由で最小 set を Taka へ。

## 注
- 本移行は「在る≠使っている」を是正する作業（新規建設が主でない）。**#6 開発作業の workcell 経由化(スライス2)が最重要**だが、まず最軽量の #1 で経路と同値検証の型を作る。
- 分析全体の grounded 根拠は本 handoff の棚卸し表（MGR 保持）。必要なら別途共有。
