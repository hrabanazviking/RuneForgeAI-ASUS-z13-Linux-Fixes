#!/bin/bash
# Team 08 - daily torch-health proof for both live venvs. Logs verdicts.
# Fixed 2026-11-12 04:15 keeper tick: previous version ended with the
# test `[ $rc -ne 0 ] && echo ALERT`, so a passing run exited 1 (test
# false = last command status) and systemd marked the service failed
# even though both venvs logged TORCH-HEALTH OK rc=0.
LOG=$HOME/ai/health/torch-health-daily.log
mkdir -p "$HOME/ai/health"
fail=0
for py in "$HOME/ai/venvs/ai-dev/bin/python" "$HOME/ai/ComfyUI/venv/bin/python"; do
  if [ -x "$py" ]; then
    out=$("$py" "$HOME/ai/bin/torch-health" 2>&1); rc=$?
    last=$(printf '%s\n' "$out" | tail -1)
    echo "$(date -Is) [$py] rc=$rc $last" >> "$LOG"
    if [ $rc -ne 0 ]; then
      fail=1
      echo "$(date -Is) ALERT torch-health FAILED for $py" >> "$LOG.alerts"
    fi
  else
    fail=1
    echo "$(date -Is) MISSING venv python: $py" >> "$LOG"
  fi
done
exit $fail
