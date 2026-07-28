# Corporate History Runtime Test Sweep

## Result

**Runtime sweep blocked.** This environment does not contain a Hearts of Iron IV executable, Steam installation, Paradox user-data directory, runtime logs, or save files. No game session was launched, so no runtime scenario is marked pass or fail and no runtime defect is claimed.

## Environment

| Item | Recorded value |
| --- | --- |
| Hearts of Iron IV version | Not available; game is not installed. The mod descriptor declares support for `1.19.*`. |
| Millennium Dawn version | Repository descriptor version `2.0.0` (`Millennium Dawn: Developer Version`). |
| Millennium Dawn upstream commit | Not independently identifiable from the local merge metadata; the repository contains upstream-sync merge `598c9750655c86423d9ce813038efbdd109fb5ff`. |
| MD-OEM commit | `6a921ae9ba4f141e25998b8cda215772833f8782` (test-report baseline). |
| Enabled DLC | Not available; no launcher or game session. |
| Enabled mods | Not available; intended clean configuration could not be created. |
| Game language | Not available; no game session. |
| Operating system | Linux `6.12.13`, x86_64. |
| Debug mode | Not enabled; game unavailable. |
| Console commands | Not used. |
| Test country | None. |
| Bookmark/start date | None. |
| Corporate-history game rule | None. |

## Test matrix

`Blocked` means the scenario requires the unavailable HOI4 runtime. It does not mean fail.

| ID | Scenario | Status | Evidence / blocker |
| --- | --- | --- | --- |
| A | 2000.1.1 — Full: United States, Japan, Taiwan, Finland, Canada, China | **Blocked** | No executable, launcher, or writable game user-data environment; no country session could be started or advanced. |
| B | 2000.1.1 — Outcomes Only | **Blocked** | No game-rule selection, popup observation, console inspection, or monthly progression possible. |
| C | 2000.1.1 — Off | **Blocked** | No game-rule selection or progression across milestone years possible. |
| D | Later January 1 starts: 2008, 2010, 2016, 2021, 2025; Full and Outcomes Only | **Blocked** | No runtime or test-bookmark session available. |
| E | Non-January starts: 2008.6.1, 2010.2.1, 2016.7.1, 2025.4.1 | **Blocked** | Temporary bookmark behavior cannot be exercised without the game. |
| F | Save/reload lifecycle at six event stages | **Blocked** | No runtime saves can be created or loaded. |
| G | Lost-event and recovery behavior | **Blocked** | Pending flags, interrupted delivery, old saves, and country invalidation cannot be manipulated in game. |
| H | AIG and Great Financial Crisis, scenarios 1–10 | **Blocked** | Crisis state, event gates, alternative routes, save/reload, Outcomes Only, and Off cannot be observed in game. |
| I | Nintendo dense-year scheduling | **Blocked** | Delivery markers, branches, late-start offsets, and Switch-era capstone cannot be observed in game. |
| J | Oracle and Google monthly catch-up | **Blocked** | New/late saves, in-flight events, expiry, reconvergence, and terminal monthly behavior cannot be observed in game. |
| K | United States multi-company concurrency | **Blocked** | Simultaneous event windows, dispatch order, AI resolution, and player-facing costs cannot be observed in game. |
| L | Collapse, civil war, annexation, tag switch, government change, invalid scope | **Blocked** | Disruption scenarios require console-enabled gameplay and saves. |
| M | Baseline, Full, Outcomes Only, Off, and late-game performance | **Blocked** | Neither clean Millennium Dawn nor MD-OEM can be launched or timed. |
| Logs | `error.log`, `game.log`, `debug.log`, `system.log` inspection | **Blocked** | No Paradox log directory or supplied runtime log bundle exists. |

## Findings

No runtime failures were reproduced. Consequently there are no defensible severity assignments, reproduction saves, runtime log citations, root-cause claims, or fixes. Static source inspection is not a substitute for the requested runtime evidence and was not used to convert any matrix item to pass or fail.

## Performance

No measurements or subjective comparisons are reported. A clean Millennium Dawn baseline and the MD-OEM Full, Outcomes Only, Off, and terminal-state runs all require the unavailable game executable. Monthly corporate work and recurring log output therefore remain unassessed.

## Artifacts

- Runtime logs: none generated or supplied.
- Saves: none generated or supplied.
- Screenshots: none; the game was not launched.
- Reproduced-defect patches: none; no runtime defect was reproduced.
- Static regression tests: none added; there was no reproduced defect to encode.

## Remaining limitations

- Every requested behavioral assertion remains unverified at runtime, including timing, popup suppression, effects, flags, variables, capstones, recovery, concurrency, invalidation, and save persistence.
- Player-visible English localisation was not rendered in game.
- Pre-existing Millennium Dawn warnings cannot be separated from MD-OEM warnings without logs from paired baseline and MD-OEM runs.
- DLC/mod load order and a clean launcher playset could not be recorded.
- Later-date and non-January development bookmarks were not created because they could not be exercised or removed after a runtime run.

## Final recommendation

**Requires remediation sweep before new companies.** Here, “remediation sweep” means completing the blocked runtime matrix in a provisioned HOI4 environment, not that the framework has been shown defective. The framework's stability remains unassessed; this report must not be treated as runtime approval.

Minimum handoff requirements for that sweep:

1. Install the descriptor-supported HOI4 build and record its exact build/hash.
2. Create clean Millennium Dawn baseline and MD-OEM playsets with identical DLC and no unrelated mods.
3. Run A–M, preserving a named save and the four requested logs for each reproduction.
4. Record objective monthly tick samples for the five performance configurations.
5. Update this matrix only from observed game sessions; attach artifacts and defect-level reproduction details before changing any item to pass or fail.
