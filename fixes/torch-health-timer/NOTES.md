# torch-health-timer — a daily scheduled proof that the GPU stack still works

**Status: applied and proven on this unit (2026-11-12). The
04:15 scheduled run fired on time and logged TORCH-HEALTH OK
for both venvs. The same run exposed — and this folder publishes
— an exit-code bug in the first version of the wrapper, fixed
and re-proven the same morning.**

## Why

The PyTorch fix for gfx1151 (see `../pytorch-gfx1151/`, whose
`torch-health.py` is the probe this timer runs) is a stack of
pins, tuned libraries and environment wiring. Any silent drift —
a package bumped here, a library path changed there — turns
into a segfault or a 3× slowdown discovered mid-work, weeks
later, with no idea when it broke. A daily scheduled proof
bounds the search to a day.

## The fix

- `torch-health-daily.sh` runs the probe (the `torch-health.py`
  from the PyTorch fix, installed on PATH) under **both** live
  venvs in turn — the main AI-dev venv and the ComfyUI venv —
  and appends one log line per venv:
  `TORCH-HEALTH OK | <GPU> | <torch version> | fp32 <x> TFLOPS |
  fp16 <y> TFLOPS | correct=True | stress50 pass`.
  A non-zero probe exit appends an ALERT line to a side log and
  makes the wrapper exit non-zero, so systemd shows the failure.
- `z13-torch-health.timer` — user timer, daily 04:15,
  `Persistent=true`.

Install:

```sh
install -m 0755 torch-health-daily.sh ~/ai/bin/torch-health-daily.sh
install -m 0644 z13-torch-health.service z13-torch-health.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now z13-torch-health.timer
```

Adjust the two venv paths in the script to your own layout.

## Proof on this unit (and the bug it caught)

- First scheduled run, 2026-11-12 04:15: both venvs logged
  `TORCH-HEALTH OK rc=0` (fp32 7.73 / 7.86 TFLOPS — the tuned
  tables' signature; stock was ~2.5) — **but systemd marked the
  service FAILED, exit 1.**
- Root cause: the wrapper's last statement was
  `[ $rc -ne 0 ] && echo ALERT …`. On a passing run the test is
  false, so the script's exit status — its last command's —
  was 1. The probe had passed; the wrapper lied.
- Fix (the published script): track a `fail` flag inside proper
  `if` blocks, capture the probe's exit before piping its
  output, and `exit $fail` explicitly.
- Re-proof: manual start after the fix finished
  `status=0/SUCCESS`, both venvs OK again (fp32 7.76 / 7.30).

## Caveats

- The probe loads the GPU for about a second per venv. Schedule
  it away from heavy GPU work; on this unit 04:15 sits clear of
  the owner's day.
- TFLOPS in the log double as a drift alarm: a sudden drop to
  ~2.5 fp32 means the tuned tables fell out of the wiring even
  if the probe still says OK.
