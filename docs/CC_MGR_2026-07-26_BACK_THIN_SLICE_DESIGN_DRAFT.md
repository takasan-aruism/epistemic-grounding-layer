# CC 管理(MGR) 設計叩き → 設計/監査(CC-α): 「拾った意図で何をするか」薄い縦串（DRAFT・叩き）

- 宛: DESIGN/AUDIT(CC-α) / 発: MGR / 2026-07-26 / TYPE=DESIGN_DRAFT（**叩き**：穴がある前提・監査が密にする・過剰/穴埋めの判断は Taka）
- 目的: 意図調べ(前者・~0.71)の**下流＝拾った意図で何をするか**を、**薄い縦串**で 1 本通す。前者の"必要精度"を後者が確定させ、初めて2DERを使って評価できる状態にする（walking skeleton）。
- 規律: **thin＝1アクションだけ end-to-end・残りは正直な stub（捏造しない）**。scope を広げない（過剰設計の回避＝Taka の警告への予防）。判断=LLM(相対二択)/構造=決定論。

## 0. 前者との接続（前提・既存）
- 前者の cheap fix（①別解書き戻し ②DEFER定義是正 ③空入力を入口で切る）は先行（別 handoff）。**④長文軸は defer**。
- 前者の出力 = Interpretation Strategy（DIRECT/CONTEXT_RESOLVE/CHOICE/BMV/INTENT_PROBE/PREMISE_PROBE/DEFER）＋不明点。

## 1. 縦串の全体（request → 意図調べ → 分岐 → 1アクション → 返し）
```
[front door submit(dogfood=我々の開発依頼)]
   └ 空入力 reject(③)
[意図調べ 4軸→7戦略(相対選別・最大2YES)]  ← 前者(既存~0.71)
   ├ INTENT_PROBE/PREMISE_PROBE → 聞き返し文を返す → STOP(ユーザ待ち)
   ├ DEFER → 保留 → STOP
   └ DIRECT/CONTEXT_RESOLVE/CHOICE/BMV → 意図は"動ける" → アクション routing へ
[アクション routing = 第2メニュー「2DERで何ができるか」]  ← 後者(本叩きの核)
   選択肢: 会話 / **検索(retrieve)** / 登録 / 実装準備 / 現状観測 …
   ※ 前者と同じ原理で選ぶ: 1呼出・相対比較・員数上限(最大1-2)・決定論集計
   └ thin slice では **retrieve だけを end-to-end で実装**・他は「未実装」と正直に返す stub
[アクション: RETRIEVE(既存 EGL)]
   └ EGL に「Xについて何が分かってる? それ既に試した?」を問い、根拠(DE番号)付きで返す
     ＋既に失敗/却下済みなら dead-approach BLOCK(既存の retention 力)
[返し = return loop → front door(record_de・generated_by_principal=CLAUDE_CODE 開示)]
```

## 2. 各層の設計（叩き）
- **A. 入口**: 我々の開発依頼を submit 経由で入れる（内部アクター）。空/空白/制御文字のみ=EMPTY_INPUT reject（③・LLM 呼ばない）。
- **B. 意図調べ**: 既存の相対選別版を流用。probe/defer なら聞き返し/保留で**止まる**（後者を呼ばない）。
- **C. アクション routing（後者の心臓・叩き）**:
  - **第2メニュー**を「2DER で今できること」で定義（会話/検索/登録/実装準備/現状観測…）。**"できること"に直結**（=1.2節 §1 の総覧と整合）。
  - 選び方は**前者と同一原理**（1呼出・相対・員数上限・決定論集計）＝設計を二重発明しない。
  - **thin: retrieve だけ実装。他は NOT_BUILT を正直に返す**（measure-first・捏造ゼロ）。
- **D. アクション=RETRIEVE**: EGL の "what's known / 既に試したか" を呼ぶ（既存・scheduler trace で実証済の力）。**新規実装は最小**。
- **E. 返し**: return loop で返却、front door 経由で記録（内部アクター開示）。

## 3. 評価（縦串を通す意味）
- 実開発依頼を1本流し、**(a)意図を掴む (b)"何が分かってる/既に試した"を返す (c)不明なら聞き返す/保留** が回るか。
- **壊れる所＝次に作る所**（DE-0066 の思想: seam で止まる・手で補完しない）。**前者の"実際に必要な精度"がここで初めて分かる**（後者が前者のバーを決める）。

## 4. 意図的に thin にしている所（過剰設計 回避・監査へ）
- アクションは**retrieve 1個だけ**。登録/実装準備/会話は stub（後で縦串が要求を出してから）。
- 前者の磨き込み（④長文軸・別解の際限ない拡張）はしない。
- retention(過去引き)は**設計のみ先行**、実装は本縦串が要求してから。

## 5. 想定される穴（自己申告・監査が密にすべき所）
- 第2メニューの網羅性（「2DERで何ができるか」の過不足＝最重要・穴が開きやすい）。
- probe で止めた後の"再開"（ユーザ返答をどう縦串に戻すか）＝DS 連携未設計。
- routing の員数上限や NO_ACTION の扱い（前者の NO_CANDIDATE と同型の穴が出るはず）。
- record_de 経由の失敗系記録（NOT_BUILT/BLOCK も残すか）。

---
*MGR 設計叩き。thin=1アクション end-to-end・残り正直 stub・判断LLM/構造決定論。監査が叩いて密に、過剰/穴埋めの線引きは Taka。★3 本線は止めない。*
