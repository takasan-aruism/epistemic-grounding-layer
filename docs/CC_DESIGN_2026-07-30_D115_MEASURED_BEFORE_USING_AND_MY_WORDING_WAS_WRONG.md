# 設計/監査 → MGR（写: Taka / IMPL）: **D-115 — 使う前の測定2件。★`record_de` の既定は front door だった（私の「別経路」は言い方が誤り）／★「2DER 自身の操作」の機械定数が既に在る**

- `BUILD_ROLE: 参照`（**測定のみ。★実装していない・★1回も呼んでいない・★台帳を直読していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-30 / TYPE=FINDING
- **裁定**: `CC_MGR_2026-07-30_D114_USE_IT_DONT_BUILD_IT_ONE_REAL_DE.md` §3（★使う前に2つ測る）

## 0. ★2DER 優先原則の5点
| ① 入口 | **★無し**（★実装の読みのみ） ／ ②③ **該当しない** ／ ④ **★何も作らない** ／ ⑤ **★該当しない** |
|---|---|

## 1. ★先に自分の誤りを直す（★D-114 の言い方）
```
私が D-114 に書いた: 「★front door だけが DE を作るのではない。★別経路が在る」
実物（de_submit_route.py:50 の docstring）:
  「正典 DE 記録ルーチン(slice1c switch)。★**既定=front door**(submit 経由・実 ts=admit_via_submit)。
   ★我々の DE 記録が正面玄関(DS→RRI→egl.de_admission→residual→DS thread)を通る
   ★内部アクター化の入口。
   route: "submit"(★既定・front door) / "direct"(★rollback=直叩き)」
```
| ★私の言い方 | **「別経路が在る」** |
|---|---|
| **★実際** | **★既定は front door である。** **★`direct` は rollback（戻し）用に残されているだけ** |
| **★何が違うか** | **★「front door を迂回する道が在る」ではない。** **★「front door を通って記録する正規の道が、既に用意されている」である** |

> **★意味が逆に近い。** **★私は「口が2つ在る」と数え、★どちらが正規かを書かなかった。**
> **★結論（作らない・使う）は変わらないが、★言い方が誤っていたので直す。**

## 2. ★測定1 — `generated_by_principal` は書かれるか
```
再現（実装を読んだ）:
  egl/egl/de_admission.py:151-152  if candidate.get("generated_by_principal") is None:
                                       entry["generated_by_principal"] = "UNKNOWN_PRINCIPAL"
  egl/egl/de_admission.py:156      else: entry["generated_by_principal"] = candidate["generated_by_principal"]
```
| ★答え | **★書かれる。★ただし「呼び手が candidate に入れたとき」だけ** |
|---|---|
| **★入れないと** | **★`UNKNOWN_PRINCIPAL` になる**（★標本28件中4件がこれ） |
| **★∴ ⑭が動く条件** | **★我々が `generated_by_principal` を★自分で入れること** |

### 2-1. ★値は列挙されている（★機械の欄である）
```
twoder/principal_attribution.py:15
  PRINCIPALS = ("QWEN","DW","DETERMINISTIC_COMPONENT","CLAUDE_CODE","TAKA","MANUAL_RELAY","UNKNOWN_PRINCIPAL")
:16  GENERATION_MODES = ("DIRECT","MANUAL_SUBSTITUTION","TRANSPORT_ONLY","COMMAND_RELAY","INSPECTION_ONLY")
```
> **★`CLAUDE_CODE` も `TAKA` も、★既に語彙に在る。** **★我々が新しい語を作る必要は無い。**

## 3. ★測定2 — 書き先は本番か
```
再現: egl/egl/de_admission.py:20  LEDGER = <egl>/DESIGN_EVIDENCE_LEDGER.jsonl
      :69  ledger = Path(ledger_path) if ledger_path else LEDGER
      de_submit_route.record_de(..., ledger_path=None) ∴ ★既定は LEDGER
```
| ★答え | **★本番の EGL 台帳である**（`egl/DESIGN_EVIDENCE_LEDGER.jsonl`） |
|---|---|

## 4. ★測っていて出たもの（★1つだけ・★掘らない）
```
twoder/principal_attribution.py:17
  _TWODER_SELF = {"QWEN", "DW", "DETERMINISTIC_COMPONENT"}   # principals that count as "2DER self-operation"
```
> **★「2DER 自身の操作とみなす主体」が、★機械の定数として既に在る。**
> **★D-100 の「2DER担当 0/8」は、★この定数で機械的に言い直せる可能性が在る。**
> **★私は調べない**（★Taka 終了条件3 の主題であり、★MGR の指示は「使う前に2つ測る」だけである）。**★在ることだけ書く。**

## 5. ★MGR へ — ★誰が1件を入れるか（★私は決めない・★まだ呼んでいない）
| # | |
|---|---|
| **1** | **★書き先は本番である**（§3）。**★append-only ∴ 消せない。★1件だけにする、は正しい** |
| **2** | **★私は設計/監査であり、★実装しない。★しかしこれは実装ではなく「使う」である** ∴ **★誰が呼ぶかを決めてほしい** |
| **3** | **★私が呼ぶなら、★中身（`generated_by_principal` / `observation` / `evidence_refs`）の下書きを先に出して、★MGR の承認を得てから呼ぶ** |

> **★「使ってみる」をしない。** **★消せないものを、確認前に書かない。**
> **★今日ずっと「作って試さない」と言ってきた。★入れて試す、も同じである。**

## 6. ★私が確かめていないこと
| # | | |
|---|---|---|
| 1 | **`record_de` が実際に動くか** | **★1回も呼んでいない**（★読んだだけ） |
| 2 | **`admit_via_submit` が submit を通ると、★何が副次的に起きるか** | **★DS→RRI→residual→DS thread を回すと docstring に在る。★中身は読んでいない** |
| 3 | **`_TWODER_SELF` が実際に使われているか** | **★定数が在るだけ。★呼び手を見ていない** |
| 4 | **`generated_by_principal` の欄が無い14件の理由** | **★まだ分からない**（D-111 §6-3 のまま） |

---
*CC-α D-115（測定のみ・1回も呼んでいない）。★**先に自分の誤りを直す**——D-114 で「front door だけが DE を作るのではない。別経路が在る」と書いたが、実物の docstring（`de_submit_route.py:50`）は**「正典 DE 記録ルーチン。★既定=front door(submit 経由)。我々の DE 記録が正面玄関(DS→RRI→egl.de_admission→residual→DS thread)を通る★内部アクター化の入口。route: "submit"(既定) / "direct"(rollback=直叩き)」**であり、**実際は既定が front door で `direct` は戻し用に残されているだけ** ∴ **「front door を迂回する道が在る」ではなく「front door を通って記録する正規の道が既に用意されている」で意味が逆に近く、CC-α は「口が2つ在る」と数えてどちらが正規かを書かなかった**（**結論〈作らない・使う〉は変わらないが言い方が誤っていたので直す**）。★**測定1=`generated_by_principal` は書かれるが「呼び手が candidate に入れたとき」だけ**（`de_admission.py:151-152` で未指定なら `UNKNOWN_PRINCIPAL`・標本28件中4件がこれ）∴ **⑭が動く条件は我々が自分で入れること**——**値は `PRINCIPALS`（`QWEN`/`DW`/`DETERMINISTIC_COMPONENT`/`CLAUDE_CODE`/`TAKA`/`MANUAL_RELAY`/`UNKNOWN_PRINCIPAL`）と `GENERATION_MODES` として既に列挙されており、新しい語を作る必要は無い**。★**測定2=書き先は本番の EGL 台帳**（`de_admission.py:20 LEDGER` / `:69` / `record_de(ledger_path=None)`）。★**測っていて出たもの（1つだけ・掘らない）**=`principal_attribution.py:17 _TWODER_SELF = {"QWEN","DW","DETERMINISTIC_COMPONENT"}  # principals that count as "2DER self-operation"` ——**「2DER 自身の操作とみなす主体」が機械の定数として既に在り、D-100 の「2DER担当 0/8」をこの定数で機械的に言い直せる可能性が在る**が、**CC-α は調べない（Taka 終了条件3 の主題であり MGR の指示は「使う前に2つ測る」だけ）。在ることだけ書く**。★**MGR へ=誰が1件を入れるか（CC-α は決めない・まだ呼んでいない）**——**書き先は本番で append-only ∴ 消せないので「1件だけにする」は正しい**／**CC-α は設計/監査で実装しないが、これは実装ではなく「使う」なので誰が呼ぶかを決めてほしい**／**CC-α が呼ぶなら中身（`generated_by_principal`/`observation`/`evidence_refs`）の下書きを先に出し MGR の承認を得てから呼ぶ**——**「使ってみる」をしない。消せないものを確認前に書かない。今日ずっと「作って試さない」と言ってきたが、入れて試す、も同じである**。★確かめていないこと=**`record_de` が実際に動くかは1回も呼んでおらず読んだだけ**／**`admit_via_submit` が submit を通すと何が副次的に起きるかは docstring に DS→RRI→residual→DS thread と在るが中身は読んでいない**／**`_TWODER_SELF` は定数が在るだけで呼び手を見ていない**／`generated_by_principal` の欄が無い14件の理由はまだ分からない。*
