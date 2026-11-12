#!/bin/bash
# Service health summary - READ ONLY. Never restarts anything.
# systemd already restarts the AI server (Restart=always) and the
# web server (on-failure); this adds the missing layer: an honest
# health verdict + failed-unit report.
echo "== service health $(date -Is) =="
for s in ollama caddy asusd supergfxd sddm; do printf '%s: %s\n' "$s" "$(systemctl is-active $s 2>&1)"; done
OV=$(curl -s -m 3 http://127.0.0.1:11434/api/version 2>/dev/null || echo UNREACHABLE)
echo "ollama http: $OV"
curl -s -m 3 -o /dev/null http://127.0.0.1:2019/config/ 2>/dev/null && echo 'caddy admin http: OK' || echo 'caddy admin http: UNREACHABLE'
echo '-- system failed units --'; systemctl --failed --no-pager 2>&1 | head -n 10
echo '-- user failed units (whoopsie templates are known noise) --'
XDG_RUNTIME_DIR=/run/user/$(id -u) systemctl --user --failed --no-pager 2>&1 | head -n 10
echo '-- eww guard --'; XDG_RUNTIME_DIR=/run/user/$(id -u) systemctl --user is-active eww-gauges-guard.timer 2>&1
tail -n 1 ~/ai/health/selfcheck.log 2>/dev/null | sed 's/^/last selfcheck line: /'
exit 0
