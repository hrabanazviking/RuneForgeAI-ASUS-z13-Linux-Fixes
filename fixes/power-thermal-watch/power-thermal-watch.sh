#!/bin/bash
# Power/thermal sampler - one sample per run, appends one line.
# hwmon resolved BY NAME at runtime (k10temp / amdgpu) - survives
# boot renumbering. The sensors fallbacks carry the proving unit's
# sensor names; check them against `sensors` on your machine.
LOG=${1:-$HOME/power-thermal.log}
hwmon_by_name(){ for d in /sys/class/hwmon/hwmon*; do [ "$(cat $d/name 2>/dev/null)" = "$1" ] && { echo "$d"; return; }; done; }
K=$(hwmon_by_name k10temp); A=$(hwmon_by_name amdgpu)
TCTL=$(cat $K/temp1_input 2>/dev/null | awk '{printf "%.1f", $1/1000}')
EDGE=$(cat $A/temp1_input 2>/dev/null | awk '{printf "%.1f", $1/1000}')
PPT=$(cat $A/power1_average 2>/dev/null | awk '{printf "%.2f", $1/1000000}')
[ -z "$PPT" ] && PPT=$(sensors amdgpu-pci-c400 2>/dev/null | awk '/PPT:/{print $2}')
FCPU=$(sensors asus-isa-000a 2>/dev/null | awk '/cpu_fan/{print $2}')
FGPU=$(sensors asus-isa-000a 2>/dev/null | awk '/gpu_fan/{print $2}')
BSTAT=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null)
BPCT=$(cat /sys/class/power_supply/BAT0/capacity 2>/dev/null)
PROF=$(cat /sys/firmware/acpi/platform_profile 2>/dev/null)
echo "$(date -Is) tctl=${TCTL:-?}C gpu=${EDGE:-?}C ppt=${PPT:-?}W fan_cpu=${FCPU:-?} fan_gpu=${FGPU:-?} bat=${BSTAT:-?}/${BPCT:-?}% profile=${PROF:-?}" >> "$LOG"
awk -v t="${TCTL:-0}" 'BEGIN{exit !(t>=95)}' && echo "$(date -Is) ALERT: CPU Tctl ${TCTL}C at/above 95C - sustained heat, check fans and load" >> "$LOG.alerts"
awk -v t="${EDGE:-0}" 'BEGIN{exit !(t>=95)}' && echo "$(date -Is) ALERT: GPU edge ${EDGE}C at/above 95C" >> "$LOG.alerts"
exit 0
