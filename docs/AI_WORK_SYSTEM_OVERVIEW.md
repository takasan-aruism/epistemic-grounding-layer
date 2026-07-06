AI Work System Overview — EGL / RRI / DS / DW
文書種別: System Overview / Conceptual Architecture
状態: CURRENT CONCEPT SUMMARY
作成目的: 本システム全体が何を解決しようとしており、EGL / RRI / DS / DWがどのように役割分担するかを、技術詳細に入る前の全体像として説明する。

1. このシステムは何か
本システムは、単一の高性能AIに調査・判断・実装・監査・記憶をすべて任せるのではなく、AIの仕事を複数の責任系へ分解し、長期的な研究・開発を壊れにくくするためのAI work systemである。

現在のAIは強い。しかし長期の研究や開発では、同じ失敗が繰り返される。

text
ユーザーの意図を取り違える
前の会話で残っていた問題を忘れる
古い情報と現在情報を混ぜる
根拠より強い結論を言う
一度通った設計を「完成」とみなす
自分で作り、自分でテストし、自分で正しいと判断する
特にESDE開発では、Claude Codeが設計・実装を行い、テストも通るが、Takaがその後に、

text
「本当に？」
「懐疑的に見て」
「前に逆だっただろ」
「そういう意味じゃない」
「あの件だよ」
と人間側から介入すると、新しい欠陥や認識ずれが発見され、結果が変わることが何度もあった。

本システムは、この人間介入を4種類へ分解し、それぞれを機構化しようとしている。

2. 4つの責任系
全体は4系統から構成される。

text
DS
Dialogue State & Continuity
= CONTINUE

RRI
Request Resolution & Research Intent
= MEAN / ASK

EGL
Epistemic Grounding Layer
= KNOW

DW
Dev Workcell
= DO
人間の介入との対応は以下。

text
「あの件だよ」
→ DS

「そういう意味じゃない」
→ RRI

「前に逆だっただろ」
→ EGL

「本当に？ 懐疑的に見て」
→ DW
この対応表が、本システム全体の最も短い説明になる。

3. DS — 対話が今どう続いているかを見る
DSはDialogue State & Continuityを扱う。

一般的なAI memory systemは、

text
short-term memory
mid-term summary
long-term memory
のように、記憶を時間長で分類することが多い。

DSは少し違う。

重要なのは、

いつ話したか

ではなく、

その対話が今も続いているか

である。

例えば5分前の質問でも、完全に回答が終わっていれば重要度は低い。

逆に3か月前の話でも、現在の開発に再び関係すれば即座に重要になる。

DSは対話を以下のような状態として扱う。

text
OPEN
ACTIVE
PARTIALLY_CLOSED
CLOSED
DORMANT
REOPENED
SUPERSEDED
例えば、

text
Windows 10の発売日は？
という質問に正しい日付を答えれば、その問いはかなり明確にCLOSEDへ近づく。

一方、

text
プーチンの今後の動向は？
は、一度回答しても必ずしもCLOSEDではない。

text
軍事
国内政治
経済
外交
時間軸
など複数のbranchが残る。

この場合は、

text
PARTIALLY_CLOSED
として、答えたscopeと未解決scopeを分けて保持する。

DSが狙うのは、

text
「あの件」
「前のやつ」
「そこじゃなくて」
「戻るけど」
「もう一点」
のような、人間には自然だがLLMには難しい参照を、単純な過去ログ検索ではなく、現在の対話状態から解決することである。

つまりDSは会話記録システムではなく、

対話状態の再構成システム

である。

4. RRI — 今の問いを何として扱うかを決める
RRIはRequest Resolution & Research Intentを扱う。

AIが調査を始める前には、実は一段重要な問題がある。

この問いは何を意味しているのか。

例えば、

text
Windows 10の発売開始日は？
は揺れが小さい。

一方、

text
プーチンの今後の動向は？
は大きく揺れる。

text
軍事なのか
政権内部なのか
経済なのか
外交なのか
何年先なのか
が不明である。

ここでAIが勝手に軍事へ固定すると、

text
「そういう意味じゃない」
となる。

逆にWindows 10の発売日を聞かれているのに過剰に分岐すれば、

text
「日付聞いてんだけど」
となる。

したがってRRIは、曖昧な問いを常に広げるのではない。

問いの揺れを見て、必要な時だけ解釈空間を開く。

初期設計では少なくとも以下を見る。

text
Context Anchoring
現在の対話との接続度

Answer Determinacy
回答空間の狭さ

Intent Breadth
合理的な意図branchの広さ

Premise Stability
問いの暗黙前提が成立している可能性
そして、

text
DIRECT
CONTEXT_RESOLVE
CHOICE
BOUNDED_MULTI_VIEW
INTENT_PROBE
PREMISE_PROBE
などのstrategyを選ぶ。

RRIのもう一つの責任は、

その問いに答えるために、何を調べる必要があるか

を設計すること。

ここではResearch Designerが、

text
Goal
Decision
Current Knowledge
Known Gaps
Failure Patterns
からResearch AxisとRQ Candidateを作る。

さらに別run / 別contextのResearch Design Auditorが、

その調査設計で本当に意思決定できるか

を監査する。

流れは以下。

text
Raw Request
↓
Request Resolution
↓
Resolved Intent
↓
Research Design
↓
Research Axes
↓
RQ Candidates
↓
Research Design Audit
↓
Approved RQ Set
つまりRRIは、

与えられた問いを調べる

だけでなく、

正しい問いの集合を作れているか

まで扱う。

5. EGL — 何を知っていて、何がまだ分からないかを管理する
EGLはEpistemic Grounding Layerである。

EGLの役割は、

AIが現在何を知っていることになっているかを、根拠・履歴・不確実性付きで管理すること

である。

一般的なRAGは、関連文書を探してLLMへ渡す。

EGLはその前後にある認識問題を扱う。

例えば、

text
検索で見つからなかった
ことと、

text
存在しない
ことは違う。

text
設計資料に書いてある
ことと、

text
実装がその通り動く
ことも違う。

text
テストでXが確認された
ことと、

text
system全体がXを保証する
ことも違う。

EGLはこれらを分ける。

主な対象は、

text
Source
Observation
Evidence
Claim
Search / Acquisition history
Currentness
Historical state
Supersession
Knowledge Gap
Failure Pattern
Source Trace
である。

例えばESDEの研究結果で、

text
probe distribution changed
が実測された。

そこから、

text
rarity premise may be shifting
はInference。

さらに、

text
attention changes the statistical frame itself
はHypothesisかもしれない。

EGLはこの3つを同じ「結果」として保存しない。

また古い主張と現在の主張を分ける。

text
旧:
memory requires persistent state

新:
historical effect may reside in weight trajectory
現在の研究TaskへはCURRENTを優先して渡す。

古い主張は削除せず、HISTORICAL / SUPERSEDEDとして保持する。

EGLの目的は、

正しい答えを必ず出すこと

ではない。

むしろ、

何を根拠に、どこまで言ってよいかを壊れにくくすること

である。

6. DW — AI開発を一人のAIにやらせない
DWはDev Workcellである。

ESDE開発では、Claude Codeがかなり優秀でも、

text
設計
↓
実装
↓
test pass
↓
完成報告
の後にTakaが、

text
「本当に？」
「懐疑的に見て」
と再確認を要求すると、追加欠陥が見つかることが何度もあった。

DWは、この人間による懐疑を工程として固定する。

全ての開発TaskをWorkcell単位で処理する。

text
PLAN
↓
GENERATE
↓
AUDIT
↓
REGENERATE
↓
UPPER REVIEW
↓
COMPLETE
初期役割は以下。

text
Claude Code
Development Manager

Qwen coding model
Coding Worker candidate

別model / 別weights / 別context
Independent Auditor / Attacker

Original Coding Worker
Reworker

Claude Code
Upper Reviewer

Python
Deterministic Workflow Gate

GPT / Claude upper tier
Exceptional Adjudicator
重要なのは、

text
generator
≠
auditor
である。

またClaude Codeが、

text
完成しました
と言っても、それだけではCOMPLETEにならない。

Python側が工程条件を確認する。

DWが試そうとしている中心仮説は、

Takaが毎回「本当に？懐疑的に見て」と言う前に、独立audit / rework loopが意味のある欠陥を見つけられるか

である。

EGL JREV-0007では先行的な類似事例が一度観測されている。

live-model adversarial suiteが全件通過した後、independent attackerが攻撃対象をdeterministic validatorへ変更し、それまで見逃されていたscope gapを発見した。

これはDW一般の有効性証明ではない。

しかし、

独立したadaptive challengeが、最初の検証面を通過した後にも新しい欠陥を発見し得る

という仮説に関連するnarrow mechanism evidenceである。

7. 4系統はどう繋がるか
基本的な流れは以下。

text
User / System
↓
DS
今どの対話が続いているか
↓
RRI
この問いを何として扱うか
何を調べる必要があるか
↓
EGL
何が現在支持され
何が古く
何が未解決か
↓
DW
その認識状態を使い
Taskを計画・実装・監査・再作業
↓
Result Packet
↓
EGL
新しいObservation / Evidence / Claim / Gap候補
ただし一方向ではない。

DSからRRIへ:

text
active threads
open branches
partial closures
reference candidates
recent intent corrections
RRIからDSへ:

text
resolved intent
retained alternatives
intent residual
research focus
answer scope
RRIからEGLへ:

text
APPROVED_RQ_SET
EGLからDWへ:

text
KNOWLEDGE_PACKET
DWからEGLへ:

text
RESULT_PACKET
DWからRRIへ:

text
RESEARCH_NEED
例えばDWがWORKER_ASSIGNMENTできないと判断した場合、Qwen Coderについて勝手にRQを作らない。

text
decision_to_support
blocked_state
missing_knowledge_hint
をRESEARCH_NEEDとしてRRIへ渡す。

RRIが、

本当にresearchが必要か。単にadapterが壊れているのではないか

をNeed Validationする。

researchが必要ならRQを設計。

EGLが調査。

Knowledge PacketがDWへ返る。

DWが再開する。

8. 共通原則 — 説明可能な変換
4系統に共通する最重要原則の一つが、

Every meaningful transformation must be explainable.

である。

対象は、

text
Raw Request
→ Resolved Intent

Dialogue Event
→ Thread State

Resolved Intent
→ Research Axis

Research Axis
→ RQ

Observation
→ Evidence

Evidence
→ Claim

Knowledge Packet
→ Implementation Packet

Finding
→ Rework

Upper Review
→ Completion Candidate
など。

ここで求めるExplainabilityは、LLMの長いchain-of-thought保存ではない。

必要なのは短い構造化記録。

text
INPUT
OUTPUT
BASIS
RETAINED UNCERTAINTY
EXCLUDED SCOPE / ALTERNATIVES
REVISION TRIGGER
である。

つまり後続AIや人間が、

text
なぜこの意図に解釈した？
なぜこのRQを作った？
なぜこのClaimを採用した？
なぜこのTaskを再作業へ戻した？
を短いtraceから再構成できること。

これはESDEで検討されていたExplainabilityの、

text
short description
stable over time
reproducible structure
という考え方を実用構造へ移したものである。

9. 共通の失敗パターン
現在、4系統を横断して最も重要なFailure Patternの一つが、

text
IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION
である。

定義:

狭いbehavior、observation、test、implementationがXを示したのに、人間またはLLMが説明時にX+へ拡張する。

例:

text
implementation X
→ guarantee X+

test X
→ property X+

answer scope X
→ intent resolved X+

branch answered X
→ thread closed X+

model installed X
→ role usable X+
このpatternはEGL開発中に複数回観測された。

例えば、

text
一部fieldでfabricated record IDを検査
していた実装が、

text
fabricated record-ID detection
と広く説明され、後に未検証fieldが見つかった。

DSでも同じことが起こり得る。

text
一branchを回答した
↓
thread closed
RRIでも、

text
context上もっともらしいintentを選んだ
↓
user intent resolved
DWでも、

text
tests passed
↓
task complete
このscope expansionを各系統で防ぐ。

10. 現在地
EGL
EGLは最も進んでいる。

現在までに、

text
Phase 1a structural enforcement spine

Phase 1b acquisition first slice
JREV-0005 remediation後review pass

Gate4 / ETB narrow structural properties

SELF_GROUNDING baseline

JREV-0007 adversarial round

Guarantee Coverage Sweep

C-TOTALITY

challenge-set drift baseline
まで進んでいる。

ただし、

text
evidence authenticity
source classification semantic correctness
general retrieval completeness
general supersession semantic accuracy
MEASURED / REPRODUCED completion
full taint lineage
autonomous RD
などは未完成または未保証。

EGLは「完成品」というより、

他の3系統を実運用しながら知識と失敗履歴を管理できる最初の基盤

まで到達した状態である。

RRI
text
Specification v0.2
NOT_IMPLEMENTED
priority HIGH
RRIは次の大型実装対象。

ただしDW walking skeleton成立後、DW最初のreal workloadとして流す。

DS
text
concept defined
Phase 0 specification draft
NOT_IMPLEMENTED
まずはintelligenceを作らない。

先に、

text
UTTERANCE
DIALOGUE_EVENT
append-only logging
provisional thread candidate
transition candidate
focus candidate
closure candidate
run metadata
を保存する。

つまり「頭脳」より先に「箱」を作る。

後でRRI / DW運用から蓄積したdialogue dataを使い、Qwen3.6でDialogue State Reconstructionを試す。

DW
text
repository created
role definition exists
bootstrap directive exists
walking skeleton NOT_IMPLEMENTED
まず最小workflowを作る。

その直後にRRI実装を最初の大型real workloadとして流す。

11. 開発順序
現在のbootstrap順序は以下。

text
1. 統合アーキテクチャをEGLへ登録

2. DS Phase 0
   従来方式で狭く実装

3. DW walking skeleton
   従来方式で最小実装

4. DWが最小Task Unitを一周可能になる

5. RRI本実装
   DW最初の大型real workloadとして実行

6. RRI開発結果をEGLへ戻す

7. DS intelligence Phase 1

8. DS → RRI Context Binding integration

9. Full DS → RRI → EGL → DW → EGL loop
重要なのは、3つを完成させてから使うのではないこと。

text
DSは記録を始める
DWは最小で動かす
RRIをDWで作る
その履歴をEGLへ入れる
実データでDSを賢くする
という順。

12. なぜEGLを中心に残り3つを作るのか
RRI、DS、DWはすべて新しい開発である。

当然失敗する。

その失敗自体をEGLへ入れる。

RRIなら、

text
Intentを早く狭めすぎた
Context Bindingがrecent contextへ偏った
Probeがresearch bypassになった
DSなら、

text
PARTIALLY_CLOSEDをCLOSEDにした
open branchを失った
「あの件」をwrong threadへ結びつけた
DWなら、

text
Qwen Coderがcross-module taskで失敗
Auditorがfixed checklistしか見なかった
COMPLETE gateがself-reportを信用した
これらをEGLへ、

text
Observation
Review Finding
Inference
Open Gap
Failure Pattern candidate
として残す。

次の開発TaskでEGLが過去failureを返す。

つまり残り3系統は、

EGLの実運用データ発生装置

でもある。

同時にEGLは、

RRI / DS / DWの共有認識基盤

になる。

13. このシステムが目指すもの
最終目標は、万能AIを一体作ることではない。

また、人間を完全に外すことでもない。

人間が現在やっている低レベルで反復的な介入を減らす。

現在Takaが何度も行っているのは、

text
「あの件だよ」
「そういう意味じゃない」
「前に逆だっただろ」
「本当に？懐疑的に見て」
である。

これは一見雑な指示だが、実際には、

text
continuity repair
intent correction
epistemic correction
independent challenge
という異なるmanagerial functionである。

本システムは、それぞれをDS / RRI / EGL / DWへ外在化する。

最終的には、

text
Taka
↓
Goal / strategic judgment
↓
AI work system
の間で、

text
context reconstruction
intent resolution
research design
evidence grounding
task decomposition
implementation
independent audit
rework
history retention
をsystem側へ移す。

人間は、

text
何を目指すか
どの価値を優先するか
重大なbranch pointで何を選ぶか
へ寄る。

14. 中心仮説
本アーキテクチャの中心仮説は、

高性能AIをさらに賢くするだけでなく、問題表現・役割分担・履歴・監査構造を外部化することで、ローカルLLMを含む複数AIの総合能力を引き上げられる可能性がある。

というもの。

例えばDSでは、

text
Claude / GPT
+ raw long conversation history
と、

text
Qwen3.6
+ Dialogue State Packet
+ bounded recent utterances
を比較できる。

DWでは、

text
Claude Codeが曖昧Taskを全部直接処理
と、

text
EGL-grounded packet
+ Claude Manager
+ Qwen Coder
+ independent Auditor
+ deterministic workflow
を比較できる。

重要なのは、

ローカルモデル単体がClaudeより賢いか

ではない。

適切な外部構造を与えた時、モデル性能差をどこまで縮められるか

である。

もし差が縮まるなら、AI能力の一部はモデル内部だけにあるのではなく、

text
memory structure
epistemic state
task representation
role separation
independent challenge
workflow enforcement
にも依存することになる。

15. 一文で言えば
このシステムは、

AIが長期の研究開発で「何の話をしているか」「何を聞かれているか」「何を本当に知っているか」「本当に完成したのか」を、それぞれ別の仕組みで管理するAI work architectureである。

より短くすると、

text
DS  = 話を見失わない
RRI = 問いを取り違えない
EGL = 知っている範囲を取り違えない
DW  = 完成を早く宣言しない
この4つを繋いだものが、現在構想しているシステム全体である。
