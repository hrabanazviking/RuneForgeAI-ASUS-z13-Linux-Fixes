# package-hygiene — orphan cleanup by name, never by blanket

**Status: method proven on this unit (2026-11-12). 114 proposed
orphans classified one by one; 52 removed by name; the rest held
on evidence. The protected stack was re-verified afterwards.**

## The trap

`apt autoremove` on a developer machine proposes removing
everything apt thinks is unneeded — including libraries that
hand-installed tools, fallback sessions, and native build setups
quietly depend on. On this unit the simulation proposed **114
packages**. Running it blind would have gambled the toolchain
to save disk the machine did not need saved.

## The method (copy this part)

1. **Simulate only:** `apt-get -s autoremove` — read the full
   list, change nothing.
2. **Classify every package by name, with evidence**, into:
   - *safe-remove* — nothing live uses it; no binary on PATH, no
     service, no build depends on it;
   - *investigate / keep for now* — grouped into the clusters
     that make blanket removal dangerous (see below).
3. **Remove only the safe set, by name**, in one explicit
   `apt remove` naming each package.
4. **Re-run the simulation** and account for everything that
   remains and everything extra apt pulled.
5. **Re-verify the protected stack** afterwards (below).

## The investigate clusters (why they were held)

- A Java/Groovy/Gradle library cluster: the machine carries a
  hand-installed Gradle and live `groovy`/`java` binaries on
  PATH — the dpkg libraries may still serve them or local
  builds, so they stay until dev-use is ruled out, not in.
- The Xorg core server: the Wayland session is separate, but an
  X fallback session may still want the core.
- Native dev headers (threading, video, OpenCL): AI/build work
  on this machine compiles against headers like these.
- A 32-bit (i386) compatibility library: held until no 32-bit
  app is shown to need it — held, not assumed.

## Result on this unit

- 114 proposed → 52 classified safe-remove, 62 investigate.
- The 52 were removed by name (apt exit 0). Apt additionally
  pulled **4 libraries from the investigate set** that were
  dependencies of the removed set — recorded honestly here
  rather than hidden: the hand-installed tools those libraries
  were held for were verified still present afterwards.
- Post-removal simulation: **58 packages remain, all in the
  investigate set**, pending dev-use evidence. They stay.
- Protected stack re-verified after removal: the display
  manager, the vendor control daemons, the local AI server and
  the web server all active; GPU driver and Mesa present; a
  Vulkan RADV probe passed; the owner's live desktop session
  was never touched.

## Caveats

- The counts are this machine's, on one day. The method is the
  reusable part; your orphan list will differ.
- "Investigate" is a destination, not a postponement trick:
  each held cluster names the evidence that would release it.
