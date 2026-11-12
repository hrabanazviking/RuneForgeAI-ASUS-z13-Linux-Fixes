# ufw-lan-firewall — LAN-first firewall, applied and proven

**Status: applied on the owner's ruling (2026-11-12) and proven
live on this unit. The ruleset below is the one running.**

## Why

The machine shipped with no host firewall active, while a web
server listened on all interfaces. The fix is a small UFW ruleset
fitted to how this machine actually lives — LAN-first, with the
owner's private overlay networks trusted — drafted from a live
socket inventory first, proposed, and applied only after the
owner ruled on it. Nothing was opened "just in case".

## Evidence base (before drafting)

Listening sockets were inventoried first. LAN-facing: a web
server on port 80 and KDE Connect on port 1716, both on all
interfaces. Everything else (a local AI server, a database, a
print service, a local proxy, the web server's admin port) was
already loopback-only and needed no rules. SSH was inactive —
nothing listened on port 22 — so the draft deliberately carries
**no SSH rule at all**.

## The ruleset (as applied)

1. Default: deny incoming, allow outgoing.
2. Port 80 allowed from the LAN subnet only (the web server is a
   LAN service, not a public one).
3. Port 1716 allowed from the LAN subnet only (KDE Connect
   pairing with the owner's own phone/tablet).
4. All incoming allowed on the Tailscale interface — the tailnet
   is the owner's private network.
5. All incoming allowed on the owner's overlay-network tunnel
   interface, after the owner explicitly ruled that overlay
   trusted alongside the tailnet. (It was first left outside the
   wall, then trusted by his word — both steps are recorded, in
   that order.)
6. No port forwarding, no allow-from-anywhere rule, no port 443
   (nothing listens on it on this machine today).

## How it was applied (the part worth copying)

A wrong first firewall rule can lock you out of your own
machine, so the application ran under the campaign's dead-man
pattern: UFW was enabled with a timed auto-disable armed, and
the disable was stood down only after proof — the firewall
reported active with the full ruleset, and the LAN web service
answered with HTTP 200 from the LAN under the firewall.

## Verify

```
sudo ufw status verbose
```

Expect: status active, default deny (incoming) / allow
(outgoing), the two LAN-only service rules, and the two trusted
interfaces.

## Caveats

- These rules fit one machine's life: a LAN web service, KDE
  Connect, a tailnet, and one trusted overlay. Copy the *method*
  (inventory first, draft, rule, apply under a dead-man, prove),
  not the exact rules, if your services differ.
- LAN-only means exactly that: off-LAN access comes through the
  tailnet or the overlay, never the open internet.
- If SSH is ever enabled later, add its rule then — LAN plus
  tailnet only, never any-source.
