# CLIENT USAGE — 2DER autonomous loop v0 (git-transported)

Claude Code は **開発環境(dev)** で動く。Taka は **クライアント環境(client)** から、GitHub を面にして
**観測**と**訂正**を行う。client の前提 = **git CLI**(python / browser 不要)。

## 観測 (observe)
```
git pull
cat docs/STATE.md          # または less docs/STATE.md / GitHub 上で閲覧
```
`docs/STATE.md` は dev 側 loop が再生成・commit する human-readable な現在状態
(latest DE / components / seals / closed branches / validation failures / **Taka decision queue** /
適用済み訂正 / UNOWNED)。

## 訂正 (correct) — append-only な machine event を出す
テキスト編集ではなく、`amend.sh` が正しい形の event を `AUTONOMY_LEDGER.jsonl` に1行追記する。
```
autonomy/amend.sh TAKA_HOLD validation_failure "RS/RS_flat の forged-id を自分で見たい"
git add AUTONOMY_LEDGER.jsonl
git commit -m "taka: HOLD validation_failure"
git push
```
アクション(7種):
`TAKA_CORRECTION` `TAKA_PRIORITY_OVERRIDE` `TAKA_HOLD` `TAKA_REJECT`
`TAKA_REDIRECT` `TAKA_AUTHORITY_RECLASSIFICATION` `TAKA_CONTEXT_ADDITION`

v0 で実際に state を動かすのは **HOLD / REJECT / PRIORITY_OVERRIDE**(candidate work に適用)。
REDIRECT / RECLASSIFICATION は decision queue に **surface されるのみ**(自動適用しない)。
CORRECTION / CONTEXT_ADDITION は **記録のみ**。可逆: 同じ target に後から event を足せば最新が勝つ。

## 反映 (effect) — dev 側
dev が `git pull` → `python3 autonomy/build_state.py`(overlay 適用)→
`python3 autonomy/state_report.py`(STATE.md 再生成)→ commit。あなたの訂正が次 loop 挙動へ入る。

## 権限境界
- **Taka authority が要る**(loop は STOP する): program disposition(research line 廃止 / objective /
  architecture / resource)· value・UX preference · 両立不能な2 route · irreversible external · 新 premise。
- それ以外の technical work は dev(Claude Code)が現物調査して進める。
- `amend.sh` / `STATE.md` は SoR(`data/`)や DE ledger を書かない。訂正は `AUTONOMY_LEDGER.jsonl` のみ、
  観測は `docs/STATE.md` のみ。生成物≠validated evidence、open gap≠false premise。
