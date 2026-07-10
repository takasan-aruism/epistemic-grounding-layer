#!/usr/bin/env bash
# SLICE-6 client amender (2DER autonomous loop v0) — PURE SHELL, no python.
# Taka (client, git CLI) emits an append-only correction event; then: git commit && git push.
# Contract: docs/autonomy_slice6_prereg_v0.1.md. Event schema matches autonomy/amend.py.
#
# Usage:  autonomy/amend.sh ACTION TARGET CONTENT [REASON]
#   ACTION ∈ TAKA_CORRECTION TAKA_PRIORITY_OVERRIDE TAKA_HOLD TAKA_REJECT
#            TAKA_REDIRECT TAKA_AUTHORITY_RECLASSIFICATION TAKA_CONTEXT_ADDITION
# Ledger path: $AUTONOMY_LEDGER or <repo>/AUTONOMY_LEDGER.jsonl
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LEDGER="${AUTONOMY_LEDGER:-$SCRIPT_DIR/../AUTONOMY_LEDGER.jsonl}"

ACTIONS="TAKA_CORRECTION TAKA_PRIORITY_OVERRIDE TAKA_HOLD TAKA_REJECT TAKA_REDIRECT TAKA_AUTHORITY_RECLASSIFICATION TAKA_CONTEXT_ADDITION"

if [ "$#" -lt 3 ]; then
  echo "usage: amend.sh ACTION TARGET CONTENT [REASON]" >&2
  echo "actions: $ACTIONS" >&2
  exit 2
fi
ACTION="$1"; TARGET="$2"; CONTENT="$3"; REASON="${4:-}"

case " $ACTIONS " in
  *" $ACTION "*) : ;;
  *) echo "amend.sh: unknown action '$ACTION'" >&2; echo "actions: $ACTIONS" >&2; exit 2 ;;
esac

# downstream_effect: HONEST about what the v0 overlay realizes (mirror amend.py)
case "$ACTION" in
  TAKA_PRIORITY_OVERRIDE) EFFECT="APPLIED: sets priority on matching candidate_executable_work" ;;
  TAKA_HOLD)   EFFECT="APPLIED: matching work item marked held (router skips)" ;;
  TAKA_REJECT) EFFECT="APPLIED: matching work item dropped" ;;
  TAKA_REDIRECT) EFFECT="SURFACED-ONLY: shown in authority_pending; task replacement NOT auto-applied in v0" ;;
  TAKA_AUTHORITY_RECLASSIFICATION) EFFECT="SURFACED-ONLY: shown in authority_pending; class change NOT auto-applied in v0" ;;
  *) EFFECT="RECORDED: kept in taka_events; no automatic state change (surfaced for review)" ;;
esac

# next AE id = high-water + 1. Portable (grep/sort, works on mawk/busybox); 10# forces base-10
# so zero-padded ids (AE-00008..) are NOT misparsed as octal (audit DEFECT B).
NEXT=1
if [ -f "$LEDGER" ]; then
  MX=$(grep -o '"event_id":[ ]*"AE-[0-9][0-9]*"' "$LEDGER" 2>/dev/null | grep -o '[0-9][0-9]*' | sort -n | tail -1 || true)
  NEXT=$(( 10#${MX:-0} + 1 ))
fi
if ! [ "$NEXT" -ge 1 ] 2>/dev/null; then
  echo "amend.sh: failed to compute next event id (aborting rather than emitting a bad id)" >&2; exit 1
fi
EID=$(printf 'AE-%05d' "$NEXT")
TS=$(date -u +%Y-%m-%dT%H:%M:%S)

# JSON-escape: delete ALL C0 control chars (0x00-0x1F incl. TAB/CR/LF) so output is always
# valid JSON that python json.loads accepts (audit DEFECT A: raw controls were silently dropped),
# then escape backslash and doublequote. NOTE: controls are STRIPPED (lossy) — NOT byte-identical
# to amend.py which escapes them as \t/\n; semantics are unaffected for human correction text.
jesc() { printf '%s' "$1" | tr -d '\000-\037' | sed 's/\\/\\\\/g; s/"/\\"/g'; }
E_TARGET=$(jesc "$TARGET"); E_CONTENT=$(jesc "$CONTENT"); E_REASON=$(jesc "$REASON")
if [ -z "$REASON" ]; then REASON_JSON="null"; else REASON_JSON="\"$E_REASON\""; fi

LINE=$(printf '{"event_id": "%s", "ts": "%s", "owner": "Taka", "action": "%s", "target_object": "%s", "content": "%s", "previous_state_ref": null, "reason": %s, "downstream_effect": "%s"}' \
  "$EID" "$TS" "$ACTION" "$E_TARGET" "$E_CONTENT" "$REASON_JSON" "$EFFECT")

printf '%s\n' "$LINE" >> "$LEDGER"
echo "$LINE"
echo "-> $LEDGER | $EID $ACTION target=$TARGET" >&2
echo "   next: git add AUTONOMY_LEDGER.jsonl && git commit -m 'taka: $ACTION $TARGET' && git push" >&2
