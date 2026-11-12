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

## Completion update (2026-11-12) — all 114 resolved by name

The investigate set has since been settled, cluster by cluster,
each on evidence — the list is now fully closed:

- **Java/Groovy cluster:** the hand-installed Gradle was proven
  self-contained (its own library tree, its own Groovy — it never
  touches the system Java libraries). With that proven, the
  owner ruled the system Groovy removed: the `groovy` package
  and its parser library were purged by name. A final census of
  the remaining 48 library jars in that cluster showed **zero
  installed reverse-dependencies outside the cluster**, and all
  48 were then removed by name in one explicit `apt remove`.
- **Kept on evidence (8 packages):** the Xorg core server and
  its mode helper (the X fallback session), a 32-bit Wayland
  server library (the installed Steam/Wine 32-bit stack), and
  five native dev headers (threading, video decode, OpenCL)
  that local AI/build trees compile against.
- **Final accounting of the original 114:** 52 removed by name
  (+4 dependent libraries apt pulled with them), 2 purged on
  the owner's ruling, 48 removed after the reverse-dependency
  census, 8 kept on evidence. Nothing was ever blanket-removed.
- The protected stack was re-verified after the final removal:
  display manager, vendor control daemons, local AI server and
  web server all active; Vulkan RADV probe passed; the
  hand-installed Gradle untouched; the live desktop session
  never disturbed.
