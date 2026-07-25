# 2DER 現状と方向性 — 総覧（2026-07-26）

- 作成: CC 管理(MGR) / 2026-07-26
- 目的: 散在する DE/handoff/進捗ドキュメントを横断し、**今の2DERが何をできて・どう開発していて・どこへ向かい・何が問題か**を1本に。
- 正直規律: 本書は as-of 2026-07-26 の実測に基づく。断定は grounded なもののみ。不明は「未確認/未実装」と明記。**"作った=効く"を主張しない**。

---

## 1. 現在の2DERの機能

### 1.1 4層認知スタック
2DER = 単一AIでなく認知を4責任系へ分解したもの（総称=2DER, EGL DE-0077）。

| 層 | = | 何をする | 状態 |
|---|---|---|---|
| **DS** (Dialogue State) | 「あの件だよ」 | 対話が今どの状態か(継続/保留/終了)を追う | Phase0+1 実装。効きは会話長依存(短会話では差なし) |
| **RRI** (Request Resolution & Research Intent) | 「そういう意味じゃない」 | 依頼の意味を汲み、何を調べるか決める | first slice 実装。**自律調査エンジンは未(GAP-XB-2)**。帳簿(科目)は2b段 |
| **EGL** (Epistemic Grounding Layer) | 「前に逆だっただろ」 | 何が確か/未確定かを管理・grounding | 最進捗。admission(de_admission)が唯一の台帳書き手 |
| **DW** (Dev Workcell) | 「本当?懐疑的に」 | 実行・独立監査・再作業 | workcell(独立監査ゲート・bypass不可)実装済。step4 live貫通 |

**full loop**(DS→RRI→EGL→DW→EGL→DS)は 2026-07-06 に1回実演済(DE-0064)。ただし**2箇所が手埋めの橋(stub)**: GAP-XB-2(RRI 調査設計)・GAP-XB-3(EGL 知識emitter)。これが埋まると「人が橋渡ししない滑らかな loop」になる。

### 1.2 正面玄関(front door) — 既に在る
- **`twoder/submit.py::submit(raw_input, conversation_id="taka-main")`**: 生入力を DS→RRI→EGL→DW→戻りループに通す本物の受付。UI=`webui.py`(:8770、"Taka→2DER であって Taka→Claude→2DER でない"と明記)。
- 実行履歴 **108件**、全て Taka の運用依頼(「本番環境を調べて」等)。**最新07-15以降アイドル**。我々の開発依頼は1件も通っていない。
- **DS→RRI→EGL が実際にできること**(実トレースで確認): 依頼を理解し、蓄積知識に照らし、**「それ既に試して失敗・却下済み」を証拠(DE番号)付きで検知してBLOCK**する。current vs 覆済み claim を区別。＝「同じ方向にまた進む」を止める本体。
- **できないこと**: 新規依頼で「自分で調査を設計して実際に調べて新知識を作る」= GAP-XB-2/3 未実装(手埋め)。

### 1.3 帳簿(account chart / RRI 2b) — 「見つける層」完成
- corpus = `rri/rri_records.jsonl`(698件、DE台帳は除外根治済)。
- **本物の話題軸4つを実証**(構造だけでは出ない=正直)。うち**2軸を凍結+命名**: `AX-72ead44e`=「Pythonモジュール実装」(114件) / `AX2-48354b9a`=「JSONLファイル解析CLI」(28件)。**142件分類/246件その他**(無理に押し込まない)。名前は別overlay台帳、凍結幾何は不変。
- 凍結は **機械propose→Taka承認**でのみ(no-auto-freeze)。
- **未実装=「働く会計」**: 仕分け+残高合わせ/保留決済/分割統合/紐付け/昇格降格/爆発弁。今の帳簿は **soft/advisory=何もgateしない**。RRI rollout では **stage 2/5**。

### 1.4 enforcement 土台(「勝手にできない」機構)
- **`twoder/authority.py`**: PRE_OP 関所。action種別を 自動実行/要承認/自動ロールバック に振る(:8005/commit/自律タスク生成/live書換 等)。承認=使い捨てトークン。
- **DW workcell**: COMPLETE前に独立監査を構造強制。**Manager(Claude)でもgateを越えられない・force_complete無し・bypass経路無し**。worker自己認証禁止。
- **sole-writer**: 各台帳に本番書き手1つ。**Claudeの直接台帳書きは"MANUAL_BYPASS"として認識される**。
- 台帳: 登記47本+structure/派生+DE台帳+LEDGER_REGISTRY。決定論 `--check` ゲート群。

---

## 2. 開発の具体的な方法（今どう作っているか）

### 2.1 マルチインスタンス体制
- **管理(MGR=Claude)** / **設計・監査(CC-α)** / **実装(IMPL)**。トポロジ = `coder─audit─designer─manager`(隣接のみ、coder↔manager 直結なし、中間audit↔designerが要)。
- **通信=egl/docs に `CC_*.md` を file 投函+watch**(INSTANCE_COMMS_PROTOCOL v0.1)。TYPE= HANDOFF/FINDING/ADJREQ/ADJRESULT/STATUS。**Takaのコピペ・リレーは廃止**。
- ループ: handoff → IMPL 実装 → AUDIT 独立再監査 → live admission → DE台帳 → **commit=Taka**。

### 2.2 規律
measure-first(出ないなら"出ない"を正当な結果に) / sole-writer分離 / 捏造ゼロ(空はUNRESOLVED) / retention>detection / drift許容と非許容の使い分け(構造は決定論・値は揺れ許容) / prompt衛生(reasoning発散はbudget増でなく入力clean) / commit=Taka。

### 2.3 ★正直な現実：今の開発は2DERを"外から侵入"して行っている
- 我々の開発は **2DER自身の機構を迂回**している:
  - DE記録 → `de_admission` **直叩き**(submit経由でない=公式bypass)。
  - 開発作業 → **Claudeインスタンス**が実施(DW workcell を迂回。workcellは在るのに使っていない)。
  - 通信 → **CC_*.md はClaudeが発明した慣行**(native機構なし)。
- ＝「2DERを使っている」でなく「外から都合よく部品をつまみ食い」。これは**orphan(配線せず忘れる)問題の根**であり、Taka が"大問題"と指摘した点。**現状は許容されるブートストラップの足場**だが恒久モードにしてはいけない。

---

## 3. 現在の開発の方向性

### 3.1 直近の到達
帳簿「見つける層」完成(DE-0537)＋P2後片付け(DE-0536 meta self-heal=commit境界で gate自動fold)。

### 3.2 現フェーズ = front door 復帰(移行A)
**「外から使う」でなく「正面玄関から入る内部アクターになる」**。我々の開発を submit 経由の正規 request として流し始める。→ 初めて2DERを"使って評価"でき、orphan再生産も構造的に止まる。

**方法(機能ごとに慎重に・A/B/C)**: Claude肩代わり機能を棚卸し済。大半は"作ってあるが迂回 or 意図的に切ってある"。
- **優先順**: ①DE記録をsubmit経由へ(第一スライス着手済・まず同値証明) → ②開発をworkcell経由へ(最重要) → ③instance間通信を確定(唯一の真の新規) → ④ポリシーゲート(commit/自律駆動)はTakaが1つずつ開放。
- **残す(C)**: 判断/上級監査(SENIOR_REVIEW=Claudeは調査推奨のみ・承認はTaka)・自由調査・自由命名。
- 基準 = 接続の容易さ + 機能の独立性(絡む=高工数)。

### 3.3 長期ゴール
Claudeが徐々に距離を取り、**最終的に上級監査(senior audit)だけ**になる。enforcement(authority.gate一般化)で **Claudeが直接台帳を読み書きできない=チートできない**構造へ。つなぎめ(front door + 上級監査)は残す。「働く会計」(B)は front door 後の RRI 主戦場として作る。

---

## 4. 現時点で考えられる問題点

1. **ブートストラップの逆説**: Claudeは"自分の直接アクセスを奪う仕組み"を直接アクセスで作るしかない。剥奪を先にやると開発が止まる。順序=固める→seam整備→移行→最後に剥奪。デリケート。
2. **"迂回の恒久化"リスク(最大)**: 便利ゆえ CC_*.md + Claudeインスタンス迂回を続けてしまう＝侵入問題の再生産。移行Aを実際に進めないと解消しない。
3. **足場 vs 本命の非対称**: 台帳/地図/gate(足場)は進むが、本命(RRI会計・自律調査)は stage2/未自律。"道具のための道具"を作る危険。監視項目。
4. **front door 未使用による半目隠し**: 我々の対話がDSに入らないため DS/RRI が材料を持てず半分目隠しで走る(実トレースで確認)。front door 復帰まで正当な評価ができない。
5. **GAP-XB-2/3 未実装**: 自律調査エンジン + EGL知識emitter。DS→RRI→EGL の"滑らかな"流れの前提。
6. **帳簿がまだ何もしない**: soft/advisory=gateしない。名前はidラベルのみ。"働く会計"は未着手。
7. **enforcement未達**: Claudeは DW以外では今もチート可能。authority.gate一般化+直叩き閉塞まで、規律は大半が"自主"であって"強制"でない。
8. **マルチインスタンス調整**: native な instance間バス無し。停止中インスタンスは人の一言(nudge)で起動(自律RD未有効)。
9. **命名/分類の限界**: 自由命名はClaude/Taka判断が残る。定型分類のみ native。

---

## 5. 主要な場所（クイックリファレンス）
- 正面玄関: `twoder/submit.py` / UI `twoder/webui.py`(:8770)
- 関所: `twoder/authority.py`(PRE_OP gate)
- 開発エンジン: `dev-workcell/dw/workcell.py`(独立監査ゲート)
- 台帳書き手: `egl/egl/de_admission.py`(sole writer) / 登記 `egl/structure/LEDGER_REGISTRY.jsonl`
- 帳簿(科目): `egl/structure/ACCOUNT_AXES_v2.json` + `ACCOUNT_AXIS_NAMES.jsonl` + `s_rthread_2br3.py`
- corpus: `rri/rri_records.jsonl`
- RRI仕様: `egl/docs/RRI_SPEC_MACHINE_v1_1.json` / 統合arch `egl/docs/AI_DEVELOPMENT_ARCHITECTURE_EGL_RRI_DS_DW_v0_1.md`
- 通信規約: `egl/docs/CC_MGR_2026-07-25_INSTANCE_COMMS_PROTOCOL_v0.1.md`
- 移行A分析+第一スライス: `egl/docs/CC_MGR_2026-07-26_FRONT_DOOR_MIGRATION_A_ANALYSIS_AND_SLICE1_HANDOFF.md`

---

## 6. RRI 設計思想と当面の心臓（2026-07-26 追記・Taka 詰め）

この節は §1.2/§3 を深掘りした当面の焦点。**既存の spec/GAP/DE に接続して記録**（新体系を作らない）。

### 6.1 RRI 設計思想（Taka）
- **2DER は硬い決定論パイプラインではない。「道具を使いこなす LLM」。** 中継の**判断は LLM がやる**（途中の判断を機械化するのは無理）。**2DER の価値＝最初から"メニュー(選択肢)"を用意すること**。良いメニューを渡せば Qwen3.6 級でも矛盾しない選択をする。
- **判断＝LLM(揺れ許容) / メニュー・構造＝2DER が決定論で用意**（[[llm_arithmetic_drift_tolerant_design]] と一致）。

### 6.2 最重要＝初手に「意図調べ」を構造で強制
- LLM(GPT/Claude 問わず)は**プロンプトを演算するだけ**で「まず意図を調べよう」と自発しない→放置で**初手で目的を取り違える**。so システムが「意図を調べる step」を**強制的に最初に挟む**必要がある。「何をするか」メニューは**意図が客観化された後**。
- これは RRI spec の Core Thesis「入口で意図を誤れば高精度で間違った仕事を実行」と同旨。

### 6.3 front RRI vs background RRI（＝別システム）
- **front RRI**（受付/分類・submit の DS→RRI→EGL）＝**作ってある**。力は「それ既に試して失敗しただろ」を証拠付きで止める *retention/block*（generation でない）。
- **background RRI**（本体・**大半未実装**）＝問い合わせを**意味分解→内外調査→必要ならEGL登録→必要ならDW呼出(設計/実装)**。EXEC_ARCH(コード構造地図)とは**無関係な別track**。

### 6.4 当面の心臓＝GAP-RRI-5（意図調べ本体・未実装）
- 具体＝RRI spec **§7 Intent Fluctuation Assessment(4軸: 文脈依存/答えの確定性/意図の広さ/前提の安定)** → **§9 Interpretation Strategy(7択メニュー: DIRECT/CONTEXT_RESOLVE/CHOICE/BOUNDED_MULTI_VIEW/INTENT_PROBE/PREMISE_PROBE/DEFER)**。**text→4軸の判定 LLM が未実装＝GAP-RRI-5**。骨(メニュー)在り・肉(LLM)無し。
- **HBB-30(preflight_gate/DE-0194)は別物**＝曖昧な量的主張1パターンを見る既製の狭いガード。意図調べ本体ではない。
- 下流の生成翼(Research Designer)＝GAP-XB-2、EGL emitter＝GAP-XB-3（[[DE-0064]] が命名）。

### 6.5 接続する過去の実証（無視しない）
- **DE-0068/0069/0071 (ODF実験)**＝背景RRIの中核実証。1観測事象から **RRI が自力で設計ニーズを生成**、独立監査が過剰主張を捕捉、**実 human 介入削減に繋がった**＝作り込む種は実証済み。
- **DE-0231**＝生成翼(:8005)を意図的に後回し＝validator在り/generation無しの根。**DE-0159**＝07-08..10 reasoning 進化が live から orphaned。
- 塩漬け実験計画 `OPERATIONAL_DESIGN_FORMATION_EXPERIMENT_PLAN.md`（この生成翼を延ばす）。

### 6.6 実地の知見（2026-07-26）
- Qwen で意図調べをやらせると**reasoning が発散**（:8005 ハング実測）＝**メニューは"発散しないほど tight"に**要設計。Taka「良いメニュー→矛盾しない選択」＋prompt衛生([[llm-prompt-hygiene-not-budget]])の実地確認。

### 6.7 役割と retention
- **Claude は RRI を"作る"（正当）が"やる"(grep/登録代行)はやめる**。登録も抽出も LLM判断+メニューで **2DER 自身**の機能に（[[ai-must-be-internal-actor-not-intruder]]）。
- **この方向は従来 MGR memory + 本doc + 会話にしか無く retention リスク**だった→本節で記録化。formal な DE/spec追補は front door 経由(dogfood)で残すのが筋。

---
*本書は living overview。大きな状態変化があれば MGR が更新する。*
