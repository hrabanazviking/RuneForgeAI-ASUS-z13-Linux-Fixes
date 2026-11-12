#!/bin/bash
# Failed-unit companion - user level, read-only reporting.
# Appends a whoopsie-filtered failed-unit report to the daily
# health log. Never restarts, resets or edits any unit.
LOG="$HOME/ai/health/failed-units.log"
mkdir -p "$(dirname "$LOG")"
{
echo "== failed-unit report $(date -Is) =="
echo "-- system failed (count) --"
systemctl --failed --no-legend --no-pager 2>/dev/null | wc -l
systemctl --failed --no-pager 2>/dev/null | head -n 5
echo "-- user failed, whoopsie-upload templates filtered as known noise --"
XDG_RUNTIME_DIR=/run/user/$(id -u) systemctl --user --failed --no-legend --no-pager 2>/dev/null | grep -v whoopsie-upload || echo "none beyond whoopsie noise"
} >> "$LOG" 2>&1
echo "wrote $LOG"
