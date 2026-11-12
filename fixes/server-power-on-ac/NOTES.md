# server-power-on-ac — OPTIONAL: never sleep on AC power

**Status: configured (preference, not a defect fix).**

> This one is **not** a repair. It encodes a deliberate choice: this
> machine doubles as an always-on server, so when it is plugged in it
> must never sleep, dim, or power-save itself into uselessness. On
> battery, normal power saving is untouched. Only take this fix if that
> trade is what you want.

## Fix

A logind drop-in, `50-server-on-ac.conf`:

```ini
[Login]
IdleAction=ignore
HandleLidSwitchExternalPower=ignore
```

- `IdleAction=ignore` — no idle-triggered sleep from logind's side.
- `HandleLidSwitchExternalPower=ignore` — closing the lid does nothing
  while on external power.

## Apply

```sh
sudo install -m 0644 50-server-on-ac.conf /etc/systemd/logind.conf.d/
sudo systemctl restart systemd-logind   # or reboot
```

## Desktop complement (KDE)

On the reference machine the KDE PowerDevil AC profile was already
compliant and is the other half of the behaviour — check yours:

- AC profile: sleep/suspend action **off**, lid action **do nothing**,
  no screen dim / turn-off, power profile **performance**
  (`powerprofilesctl get` → `performance`).

Logind rules don't stop a desktop power manager from sleeping the
machine on its own timers; both layers have to agree.

## Verify

On AC: close the lid / walk away — the machine stays up and reachable.
On battery: normal sleep behaviour returns.

## Caveats

- A server that never sleeps also never saves that power. That's the
  point of the preference; don't apply it to a machine you carry.
