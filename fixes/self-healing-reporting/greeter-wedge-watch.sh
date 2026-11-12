#!/bin/bash
# Greeter-wedge detector - LOG-ONLY version.
# Implements the greeter GPU-wedge signature (>=5 ring gfx_0.0.0
# timeouts with the greeter faulting, inside 120s). This version
# NEVER restarts the display manager: a 24h live log-only dry-run
# must complete clean before any restart action may be enabled,
# and enabling that is a later, separate step.
# Usage:
#   greeter-wedge-watch.sh --live
#   greeter-wedge-watch.sh --replay BOOT SINCE UNTIL SESSION(active|none)
LOG="$HOME/greeter-wedge.log"
mkdir -p "$(dirname "$LOG")"
cnt() { journalctl -k -b "$1" --since "$2" --until "$3" --no-pager 2>/dev/null | grep -c 'ring gfx_0.0.0 timeout'; }
flt() { journalctl -k -b "$1" --since "$2" --until "$3" --no-pager 2>/dev/null | grep -c 'Process sddm-greeter'; }
if [ "$1" = "--live" ]; then
  NOW=$(date '+%Y-%m-%d %H:%M:%S'); WIN=$(date -d '120 seconds ago' '+%Y-%m-%d %H:%M:%S')
  C=$(cnt 0 "$WIN" "$NOW"); F=$(flt 0 "$WIN" "$NOW")
  if loginctl list-sessions --no-pager 2>/dev/null | grep -q ' user '; then SESS=active; else SESS=none; fi
  if [ "$C" -ge 5 ] && [ "$F" -ge 1 ]; then
    if [ "$SESS" = active ]; then echo "$(date -Is) SIGNATURE-BUT-SESSION-ACTIVE count=$C greeter=$F -> REFUSE (log-only)" >> "$LOG";
    else echo "$(date -Is) SIGNATURE count=$C greeter=$F -> WOULD-RESTART-SDDM (log-only, action disabled)" >> "$LOG"; fi
  fi
  exit 0
fi
if [ "$1" = "--replay" ]; then
  C=$(cnt "$2" "$3" "$4"); F=$(flt "$2" "$3" "$4")
  echo "replay boot=$2 window=$3..$4 timeouts=$C greeter_faults=$F assumed_session=$5"
  if [ "$C" -ge 5 ] && [ "$F" -ge 1 ]; then
    if [ "$5" = active ]; then echo "VERDICT: REFUSE (session active)"; else echo "VERDICT: FIRE (signature, no session)"; fi
  else echo "VERDICT: NO-FIRE (below signature)"; fi
  exit 0
fi
echo "usage: --live | --replay BOOT SINCE UNTIL active|none" >&2; exit 2
