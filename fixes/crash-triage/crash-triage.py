#!/usr/bin/env python3
"""crash-triage: quarantine sandbox/experiment apport reports, leave real ones.

Watches /var/crash. For each new settled *.crash file it classifies:
  SANDBOX -> move to ~/.local/state/crash-triage/quarantine/ + digest line
  REAL    -> leave untouched (default; any doubt is REAL)
See DESIGN.md in ~/z13-fix-forge/team-07/crash-triage/ for the full design.
Stdlib only.
"""
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime

CRASH_DIR = "/var/crash"
STATE_DIR = os.path.expanduser("~/.local/state/crash-triage")
QUAR_DIR = os.path.join(STATE_DIR, "quarantine")
DIGEST = os.path.join(STATE_DIR, "digest.log")
WLOG = os.path.join(STATE_DIR, "watcher.log")
POLL_S = 1.0

FORGE_MARKERS = ("aesir-", "mimiralloc", "samverk-", "mythic-", "-forge", "/build/")
SESSION_SLICE_RE = re.compile(r"/user@\d+\.service/(session|background)\.slice/")
TOOLING_CGROUP = "musegadget.service"


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def log(path, line):
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def parse_crash(path):
    """Return (fields dict, raw text). Missing/unreadable -> ({}, '')."""
    try:
        with open(path, "rb") as fh:
            raw = fh.read().decode("utf-8", "replace")
    except OSError:
        return {}, ""
    fields = {}
    for key in ("ExecutablePath", "ProcCmdline", "ProcCwd", "Signal", "SignalName", "Date"):
        m = re.search(r"^" + key + r": ?(.*)$", raw, re.M)
        if m:
            fields[key] = m.group(1).strip()
    return fields, raw


def experiment_path(text):
    if not text:
        return False
    if text.startswith("/tmp/") or " /tmp/" in text:
        return True
    return any(m in text for m in FORGE_MARKERS)


def coredump_cgroup(exe, date_str):
    """Best-effort Control Group for the coredump matching exe+time. '' if unknown."""
    try:
        out = subprocess.run(
            ["coredumpctl", "list", "--no-pager"],
            capture_output=True, text=True, timeout=10,
        ).stdout
    except Exception:
        return ""
    target_ts = None
    if date_str:
        for fmt in ("%a %b %d %H:%M:%S %Y", "%b %d %H:%M:%S %Y"):
            try:
                target_ts = datetime.strptime(date_str.strip(), fmt).timestamp()
                break
            except ValueError:
                pass
    best_pid, best_dt = None, 1e18
    line_re = re.compile(
        r"^\w{3}\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+\S+\s+(\d+)\s+\d+\s+\d+\s+\S+\s+\S+\s+(.+?)\s+[\d.]+[KMG]?$"
    )
    for line in out.splitlines():
        m = line_re.match(line.strip())
        if not m:
            continue
        day, tod, pid, exe_path = m.groups()
        if exe_path.strip() != exe:
            continue
        try:
            ts = datetime.strptime(day + " " + tod, "%Y-%m-%d %H:%M:%S").timestamp()
        except ValueError:
            continue
        if target_ts:
            dt = abs(ts - target_ts)
            if dt < best_dt:
                best_dt, best_pid = dt, pid
        elif best_pid is None or ts >= 0:
            # no report time to match: take the most recent matching dump
            best_pid = pid
            best_dt = 0
    if best_pid is None or (target_ts and best_dt > 120):
        return ""
    try:
        info = subprocess.run(
            ["coredumpctl", "info", best_pid, "--no-pager"],
            capture_output=True, text=True, timeout=10,
        ).stdout
    except Exception:
        return ""
    m = re.search(r"Control Group:\s*(\S+)", info)
    return m.group(1) if m else ""


def classify(fields, raw, cgroup):
    """Return ('SANDBOX'|'REAL', [reasons]). Fail-safe: default REAL."""
    exe = fields.get("ExecutablePath", "")
    cmd = fields.get("ProcCmdline", "")
    cwd = fields.get("ProcCwd", "")
    if cgroup and SESSION_SLICE_RE.search(cgroup):
        return "REAL", ["R1:session-service-cgroup"]
    reasons = []
    if cgroup and TOOLING_CGROUP in cgroup:
        reasons.append("S1:tooling-cgroup")
    if experiment_path(cmd):
        reasons.append("S2:cmdline-experiment-path")
    if cwd and (cwd.startswith("/tmp") or experiment_path(cwd)):
        reasons.append("S3:cwd-experiment-tree")
    if "QT_QPA_PLATFORM=offscreen" in raw or "QT_QPA_PLATFORM:offscreen" in raw:
        reasons.append("S4:offscreen-test-instance")
    if exe and (exe.startswith("/tmp/") or experiment_path(exe)):
        reasons.append("S5:exe-experiment-tree")
    if reasons:
        return "SANDBOX", reasons
    return "REAL", ["default:real"]


def process_file(name):
    path = os.path.join(CRASH_DIR, name)
    fields, raw = parse_crash(path)
    if not fields:
        log(WLOG, f"{now_iso()} LEAVE {name} reason=unparseable")
        return
    cgroup = coredump_cgroup(fields.get("ExecutablePath", ""), fields.get("Date", ""))
    verdict, reasons = classify(fields, raw, cgroup)
    exe = fields.get("ExecutablePath", "?")
    sig = fields.get("SignalName") or fields.get("Signal") or "?"
    if verdict == "SANDBOX":
        dest = os.path.join(QUAR_DIR, name)
        if os.path.exists(dest):
            # apport reuses filenames; never overwrite an earlier quarantine
            dest = os.path.join(
                QUAR_DIR, name[: -len(".crash")] + f".{int(time.time())}.crash"
            )
        try:
            shutil.move(path, dest)
        except OSError as exc:
            log(WLOG, f"{now_iso()} LEAVE {name} exe={exe} move-failed={exc}")
            return
        for suffix in (".upload", ".uploaded"):
            side = os.path.join(CRASH_DIR, name[: -len(".crash")] + suffix)
            if os.path.exists(side):
                try:
                    shutil.move(side, os.path.join(QUAR_DIR, os.path.basename(side)))
                except OSError:
                    pass
        log(DIGEST, f"{now_iso()} QUARANTINE file={name} exe={exe} signal={sig} "
                    f"reasons={','.join(reasons)} cgroup={cgroup or 'unknown'}")
        log(WLOG, f"{now_iso()} QUARANTINE {name} exe={exe} signal={sig} reasons={','.join(reasons)}")
    else:
        log(WLOG, f"{now_iso()} REAL {name} exe={exe} signal={sig} reasons={','.join(reasons)} cgroup={cgroup or 'unknown'}")


def main():
    os.makedirs(QUAR_DIR, exist_ok=True)
    log(WLOG, f"{now_iso()} START crash-triage watcher pid={os.getpid()}")
    seen = {}   # name -> (size, mtime, stable_polls)
    done = set()  # (name, size, mtime) fingerprints already processed.
    # NOTE: apport reuses the same filename for repeat crashes of one
    # executable (CrashCounter inside the file), so identity is the
    # fingerprint, never the name alone.
    while True:
        try:
            names = [n for n in os.listdir(CRASH_DIR) if n.endswith(".crash")]
        except OSError:
            names = []
        for name in names:
            path = os.path.join(CRASH_DIR, name)
            try:
                st = os.stat(path)
            except OSError:
                continue
            if (name, st.st_size, st.st_mtime) in done:
                continue
            prev = seen.get(name)
            if prev and prev[0] == st.st_size and prev[1] == st.st_mtime:
                stable = prev[2] + 1
                seen[name] = (st.st_size, st.st_mtime, stable)
                if stable >= 2:
                    done.add((name, st.st_size, st.st_mtime))
                    try:
                        process_file(name)
                    except Exception as exc:  # never die on one bad file; leaving it = REAL
                        log(WLOG, f"{now_iso()} LEAVE {name} error={exc!r}")
            else:
                seen[name] = (st.st_size, st.st_mtime, 0)
        for name in list(seen):
            if name not in names:
                del seen[name]
        time.sleep(POLL_S)


if __name__ == "__main__":
    sys.exit(main())
