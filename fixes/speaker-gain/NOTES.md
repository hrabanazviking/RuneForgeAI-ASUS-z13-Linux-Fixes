# speaker-gain — the CS35L41 amps' quiet firmware profile

**Status: applied and structurally proven** (the kernel's probe
reads the new gain back — twice). Whether it *sounds* right is a
judgement for your own ears; this page proves the setting, not
the taste.

## Symptom

The internal speakers (Cirrus Logic CS35L41 amplifiers, ALC294
codec) are noticeably quiet under Linux, even at full volume.

## Cause

Each amp loads a DSP speaker-protection tuning (a "bincfg") chosen
by a firmware symlink. On this machine those links point at the
**15_5dB** profile — matching the amps' boot-time probe line
"Gain: 15" — the quiet end of the profiles ASUS ships in the
machine's own Cirrus firmware set. A **19_5dB** profile ships in
the same set; nothing selects it by default.

## Fix

Repoint both speaker-protection links (left `l0`, right `r0`) at
the 19.5 dB profile:

```sh
sudo ln -sf cs35l41/bincfgs/cs35l41-dsp1-19_5dB.bincfg.zst /lib/firmware/cirrus/cs35l41-dsp1-spk-prot-10431fb3-l0.bincfg.zst
sudo ln -sf cs35l41/bincfgs/cs35l41-dsp1-19_5dB.bincfg.zst /lib/firmware/cirrus/cs35l41-dsp1-spk-prot-10431fb3-r0.bincfg.zst
```

**Before you change anything**, record where your links point
now — that record *is* your rollback:

```sh
readlink /lib/firmware/cirrus/cs35l41-dsp1-spk-prot-10431fb3-l0.bincfg.zst
readlink /lib/firmware/cirrus/cs35l41-dsp1-spk-prot-10431fb3-r0.bincfg.zst
```

The profile takes effect when the amps re-probe: an i2c
unbind/bind of the amp devices reloads them without a reboot, and
a plain reboot does it too. Restart PipeWire/WirePlumber
afterwards and confirm the default sink is the ALC294 analog
speakers.

## Verify

The kernel probe names the loaded gain. After the swap on the
reference machine, both amps read back **"Gain: 19"** — once at an
i2c re-probe in the same session, and again at the next boot's
probe, so the setting is durable, not a one-off.

## Rollback (two commands, fully reverses it)

```sh
sudo ln -sf cs35l41/bincfgs/cs35l41-dsp1-15_5dB.bincfg.zst /lib/firmware/cirrus/cs35l41-dsp1-spk-prot-10431fb3-l0.bincfg.zst
sudo ln -sf cs35l41/bincfgs/cs35l41-dsp1-15_5dB.bincfg.zst /lib/firmware/cirrus/cs35l41-dsp1-spk-prot-10431fb3-r0.bincfg.zst
```

Then re-probe or reboot, and the probe reads "Gain: 15" again.

## Caveats

- The identifier in the link names (`10431fb3`) is this model's
  amp configuration id — check your own links before assuming the
  same names on a different unit.
- The source recipe warns that above ~80% volume the louder
  profile may distort bass slightly. That's the trade the 19.5 dB
  profile makes; the 15_5 dB rollback above is painless if your
  ears vote the other way.
