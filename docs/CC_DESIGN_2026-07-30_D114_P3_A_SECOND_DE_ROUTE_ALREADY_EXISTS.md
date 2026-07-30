# 設計/監査 → MGR（写: Taka / IMPL）: **P-3 調査 — ★front door だけが DE を作るのではない。★`route=` を持つ口が★既に在る（実装しない）**

- `BUILD_ROLE: 参照`（**調査のみ。★実装していない・★投入していない・★台帳を直読していない・★1本も走らせていない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-30 / TYPE=FINDING
- **裁定**: `CC_MGR_2026-07-30_D113_THE_ROOT_IS_THAT_WE_DEVELOP_OUTSIDE_2DER.md` §4（★測ることは1つだけ）

## 0. ★2DER 優先原則の5点
| ① 入口 | **★無し**（★これは 2DER への問いではなく、★2DER 自身の実装の調査である） |
|---|---|
| ②③ | **★該当しない** ／ ④ **★何も実装しない**（Taka: 調査する） ／ ⑤ **★該当しない** |

## 1. ★答え（★1行）
> **★front door を通ったものだけが DE になるのではない。**
> **★`egl/structure/de_submit_route.py` に、★`route=` を引数に持つ口が★既に在り、★3本のスクリプトが使っている。**

## 2. ★測ったこと（★述語を1つ・1回 走査）
```
★述語: 「.py を構文木で解析し、呼び出し名が `admit_design_evidence` である Call ノード」
★走査: 全5repo・.py 全件・打ち切り無し
★総数: ★8件

  ★front door（twoder/submit.py:142）      ★1
  ★egl/structure スクリプト                 ★2   ← de_submit_route.py:67 / s_de_route_equiv.py:74
  テスト                                     5
```
> **★`admit_design_evidence` は「唯一の書き手」である**（資料 §5.5）。**★その呼び手が8件しかない。**
> **★そのうち front door は1件だけである。**

## 3. ★別経路の実体（★実物を読んだ）
```
egl/structure/de_submit_route.py が公開している関数:
  :37  def admit_via_submit(candidate, ts=None, ledger_path=None)
  :50  def record_de(candidate, ts=None, ledger_path=None, ★route=None)
```
| | |
|---|---|
| **★`route=` という欄が在る** | **★「どの経路で作ったか」を、★最初から書けるようになっている** |
| **★`ledger_path=None`** | **★既定は本番の台帳である**（★逃がしていない） |
| **★使っているもの（全5repo 走査）** | `s_front_door_bypass_inventory.py` ／ `s_de_route_equiv.py` ／ `s_corpus_provenance.py` の★3本 |

> **★`admit_via_submit` という名前がすでに「submit 経由で入れる」を指している。**
> **★`s_de_route_equiv.py`（DE route equivalence）は、★2つの経路が同じかを比べる作りに見える。**
> **★私は開いていない**（★C を掘らない）。**★名前から読める範囲だけ書く。**

## 4. ★∴ MGR §4 の問いへの答え
| ★問い | **「front door を通ったものだけが DE になるのか。★それとも別経路でも DE になるのか」** |
|---|---|
| **★答え** | **★別経路でも DE になる。★その口は既に在り、★`route=` まで持っている** |
| **★∴ 決まること** | **★「我々の開発を記録するには front door を通すしかない」は★成り立たない** |

## 5. ★私が書かないこと（★先に出す）
| ★書かない | 理由 |
|---|---|
| **「だから我々の開発を記録できる」** | **★使っていない。★1回も呼んでいない。★動くかは確かめていない** |
| **「front door を通さなくてよい」** | **★経路が在ることと、★どちらを通すべきかは別である。★決めるのは MGR と Taka** |
| **「あと1段で記録できる」** | **★今日ずっと禁じてきた形。★書かない** |
| **「`CLAUDE_CODE` の10件はこの経路で作られた」** | **★確かめていない**（§6-1） |

### 5-1. ★1つだけ、事実として添える（★提案ではない）
```
★`record_de(..., ledger_path=None)` の既定は★本番の台帳である。
∴ ★もし使うなら、★それは「本番に書く」ことである。
```
> **★これは今日 `G-77` で数えた「本番の記録に書くか」と★同じ述語に当たる。**
> **★使うかどうかを決めるとき、★この1行を一緒に見てほしい。**

## 6. ★私が確かめていないこと
| # | | |
|---|---|---|
| **1** | **既存の DE が★どちらの経路で作られたか** | **★front door から見える DE の欄に `route` が無い**（実測: 欄は10種で `route` を含まない）∴ **★既存の DE を経路で分けられない** |
| 2 | **`de_submit_route` の中身が実際に動くか** | **★読んでいない。★呼んでいない** |
| 3 | **`s_de_route_equiv.py` が何を比べているか** | **★名前から読んだだけ。★開いていない** |
| 4 | **テスト5件が本番の台帳に DE を書くか** | **★見ていない**（★`G-77` の61本に含まれるかは未確認） |

> **★1が重い。** **★「別経路が在る」と言えるが、★「既存の DE のどれがそれで作られたか」は言えない。**
> **★`generated_by_principal` は「誰が」を持つが、★`route` は front door に出ていない。**

---
*CC-α P-3 調査（実装なし・1本も走らせていない）。★**答え=front door を通ったものだけが DE になるのではなく、`egl/structure/de_submit_route.py` に `route=` を引数に持つ口が既に在り3本のスクリプトが使っている**。★測ったこと=**述語「構文木で `admit_design_evidence` の呼び出し」を1つ決めて全5repo・.py 全件・打ち切り無しで1回 走査 → 総数8件**（**front door(`twoder/submit.py:142`) 1／egl/structure スクリプト 2／テスト 5**）——**`admit_design_evidence` は資料 §5.5 が「唯一の書き手」と記す関数で、その呼び手が8件しかなくうち front door は1件だけ**。★**別経路の実体（実物を読んだ）**=`de_submit_route.py:37 admit_via_submit(candidate, ts, ledger_path)` と **`:50 record_de(candidate, ts, ledger_path, ★route=None)`** で、**`route=` という「どの経路で作ったか」を最初から書ける欄が在り**、**`ledger_path=None` の既定は本番の台帳（逃がしていない）**、使っているのは `s_front_door_bypass_inventory.py`／`s_de_route_equiv.py`／`s_corpus_provenance.py` の**3本**——**`admit_via_submit` という名前が既に「submit 経由で入れる」を指し、`s_de_route_equiv.py`（DE route equivalence）は2つの経路が同じかを比べる作りに見えるが CC-α は開いておらず名前から読める範囲だけ書く**。★**∴ MGR の問いへの答え=別経路でも DE になり、その口は既に在り `route=` まで持っている** ∴ **「我々の開発を記録するには front door を通すしかない」は成り立たない**。★**書かないこと**=「だから我々の開発を記録できる」（**使っておらず1回も呼んでおらず動くかは確かめていない**）／「front door を通さなくてよい」（**経路が在ることとどちらを通すべきかは別で、決めるのは MGR と Taka**）／「あと1段で記録できる」／「`CLAUDE_CODE` の10件はこの経路で作られた」（**確かめていない**）。★**1つだけ事実として添える（提案ではない）**=**`record_de(..., ledger_path=None)` の既定は本番の台帳**なので**もし使うならそれは「本番に書く」ことであり、今日 `G-77` で数えた「本番の記録に書くか」と同じ述語に当たる**——**使うかどうかを決めるときこの1行を一緒に見てほしい**。★確かめていないこと=**既存の DE がどちらの経路で作られたかは、front door から見える DE の欄10種に `route` が無いので分けられない（これが最も重い。`generated_by_principal` は「誰が」を持つが `route` は front door に出ていない）**／`de_submit_route` の中身が実際に動くかは読んでも呼んでもいない／`s_de_route_equiv.py` は名前から読んだだけ／**テスト5件が本番の台帳に DE を書くかは未確認（`G-77` の61本に含まれるかも未確認）**。*
