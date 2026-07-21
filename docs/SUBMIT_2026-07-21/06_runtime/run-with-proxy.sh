#!/usr/bin/env bash
# run-with-proxy.sh <name>  — invoked ONLY by workcell-runner@<name>.service (%i = <name>).
# TRUST-PATH glue. The R-5 fix moved instance selection from a sudoers wildcard to THIS
# script's NAME validation, so it must be airtight: validate before ANY use, fail-closed,
# never interpolate untrusted text into a directory, never run the runner on a bad state.
# It stands up the stage-2 in-namespace loopback bridge (socat TCP 127.0.0.1:8005 ->
# bound unix socket -> host vLLM) required because the immutable runner speaks HTTP/TCP
# (D-1 finding, DE-0441), then runs the unmodified runner and cleans the socat up.
set -euo pipefail

SRV="/srv/workcell"
PACKETS="$SRV/packets"
RUNNER="$SRV/bin/runner.py"
RUNS="$SRV/runs"
VLLM_SOCK="/run/vllm/qwen.sock"
LOOPBACK_PORT=8005
PY=/usr/bin/python3

NAME="${1:-}"

# 1) NAME validation FIRST, before any use. bash [[ =~ ]] anchors the WHOLE string (grep's
#    '$' matches end-of-LINE, so a newline-embedded name like $'M1\nx' would slip past grep —
#    a real validation-bypass class; bash regex rejects it). Any mismatch => fail-closed.
if [[ ! "$NAME" =~ ^[A-Za-z0-9_-]+$ ]]; then
  echo "run-with-proxy: REJECT instance name (must match ^[A-Za-z0-9_-]+\$, whole-string): '${NAME}'" >&2
  exit 64
fi

# 2) Packet path = fixed-template concatenation ONLY. Then realpath-confine under $PACKETS
#    (defence in depth; the regex already forbids '/', '.', '..' so no traversal is possible).
PACKET="$PACKETS/$NAME.json"
RESOLVED="$(realpath -m -- "$PACKET")"
PACKETS_REAL="$(realpath -m -- "$PACKETS")"
case "$RESOLVED" in
  "$PACKETS_REAL"/*) : ;;
  *) echo "run-with-proxy: REJECT packet path escapes $PACKETS_REAL: $RESOLVED" >&2; exit 65 ;;
esac
if [ ! -f "$PACKET" ]; then
  echo "run-with-proxy: packet not found: $PACKET" >&2; exit 66
fi

# 3) Preconditions: the host proxy socket must already exist (proxy up). Else refuse — we do
#    NOT run the runner without a vLLM path.
if [ ! -S "$VLLM_SOCK" ]; then
  echo "run-with-proxy: vLLM socket absent ($VLLM_SOCK); refusing to run" >&2; exit 69
fi

# 4) Stage-2 socat: loopback TCP:8005 -> bound unix socket. Started in background; a trap
#    guarantees it is killed on ANY exit (no residue). If it fails to come up, the runner
#    is NOT started.
SOCAT_PID=""
cleanup() { [ -n "$SOCAT_PID" ] && kill "$SOCAT_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

socat "TCP4-LISTEN:${LOOPBACK_PORT},bind=127.0.0.1,fork,reuseaddr" \
      "UNIX-CONNECT:${VLLM_SOCK}" &
SOCAT_PID=$!

# wait (bounded, ~5s) for the loopback listener; abort if socat dies.
ready=0
for _ in $(seq 1 50); do
  if ! kill -0 "$SOCAT_PID" 2>/dev/null; then
    echo "run-with-proxy: stage-2 socat exited during startup" >&2; exit 70
  fi
  if (exec 3<>"/dev/tcp/127.0.0.1/${LOOPBACK_PORT}") 2>/dev/null; then
    exec 3>&- 3<&- 2>/dev/null || true; ready=1; break
  fi
  sleep 0.1
done
if [ "$ready" -ne 1 ] || ! kill -0 "$SOCAT_PID" 2>/dev/null; then
  echo "run-with-proxy: stage-2 socat not ready on 127.0.0.1:${LOOPBACK_PORT}" >&2; exit 70
fi

# 5) Run the IMMUTABLE runner on the mapped packet. NOT exec'd, so the EXIT trap runs and
#    reaps the socat. The runner writes its run_dir (run_log.jsonl + RESULT_PACKET.json)
#    under $RUNS (the unit's only writable path).
set +e
"$PY" "$RUNNER" "$PACKET" --runs-root "$RUNS"
rc=$?
set -e
exit "$rc"
