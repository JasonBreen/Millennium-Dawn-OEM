# France Corporate Systems

This module adapts the supplied *MD-OEM France: Implementation-Ready Event Specification for Alcatel, STMicroelectronics, and France Télécom/Orange* to the repository's Corporate History framework. It keeps the specification's interconnected-company model while using the installed mod's 0-10 state scale, game-rule gates, yearly dispatcher, monthly reconstruction, English-only localisation, and mutually exclusive outcome ideas.

## Content Contract

- Namespace: `FRA_corporate_systems_events`.
- Visible content: 24 new events plus existing `FRA_nokia_response_events.1`, for 25 player-facing events.
- Hidden content: `FRA_corporate_systems_events.90`, a reward-free reconstruction anchor.
- State: ten country variables, initialized once and clamped from 0 through 10 after every mutation.
- Modes: Full shows events; Outcomes Only reconstructs the historical path without event rewards; Off creates no France Corporate Systems state.
- Outcomes: five mutually exclusive national ideas, chosen from the final bounded state. The idea is the authoritative outcome state; no duplicate outcome flag is written.
- External handoff: the existing Nokia response ID and FIN callbacks remain stable. France-owned adapter effects record the local outcome before the FIN-owned transaction event receives its callback.

## Event Map

| ID | Chain | Milestone |
| --- | --- | --- |
| `.1` | Alcatel | Telecom-market collapse and restructuring |
| `.2` | Alcatel / ST | Alcatel Microelectronics divestiture |
| `.3` | Alcatel | Lucent combination |
| `.4` | Alcatel | Merger-integration reset |
| `.5` | Alcatel | Refinancing and the credit wall |
| `.6` | Alcatel | Shift Plan |
| `FRA_nokia_response_events.1` | Alcatel / Nokia | France's 2015 transaction response |
| `.7` | Alcatel / Nokia | French research pillar inside Nokia |
| `.10` | STMicroelectronics | Purchase of Alcatel Microelectronics |
| `.11` | STMicroelectronics | Crolles2 alliance expansion |
| `.12` | STMicroelectronics | Strategy after Crolles2 |
| `.13` | STMicroelectronics | ST-NXP Wireless |
| `.14` | STMicroelectronics | ST-Ericsson formation |
| `.15` | STMicroelectronics | Downturn and Nano2012 support |
| `.16` | STMicroelectronics | ST-Ericsson unwind |
| `.17` | STMicroelectronics | European microelectronics IPCEI |
| `.20` | France Télécom / Orange | Orange acquisition |
| `.21` | France Télécom / Orange | MobilCom exposure and debt crisis |
| `.22` | France Télécom / Orange | Ambition FT 2005 |
| `.23` | France Télécom / Orange | State minority ownership |
| `.24` | France Télécom / Orange | Converged broadband buildout |
| `.25` | France Télécom / Orange | Orange group identity |
| `.26` | France Télécom / Orange | National fiber investment |
| `.27` | France Télécom / Orange | 5G vendor selection |
| `.28` | Cross-company | Conditional Huawei authorization pressure |

The yearly dispatcher owns the normal visible delivery windows. Startup scheduling covers the current start year, while the monthly France driver repairs a genuinely lost delivery and advances reward-free reconstruction. Events remain `is_triggered_only = yes`; they are never date polled globally.

The ST-NXP choice (`.13`) becomes player-visible on April 10, 2008, when the proposal is actionable. Outcomes Only records the historical consolidation on August 1, 2008, matching the source's separate operational-transition date.

## State Model

| Variable | Baseline | Meaning |
| --- | ---: | --- |
| `FRA_corporate_strategic_sovereignty` | 6 | French control of critical research, production, and infrastructure |
| `FRA_corporate_european_integration` | 5 | Depth of European industrial and technology cooperation |
| `FRA_corporate_telecom_capacity` | 6 | Domestic telecom-equipment and network-system capability |
| `FRA_corporate_semiconductor_capacity` | 6 | French-linked semiconductor capability |
| `FRA_corporate_digital_infrastructure` | 4 | Broadband, mobile, and core-network deployment |
| `FRA_corporate_alcatel_health` | 6 | Alcatel and Alcatel-Lucent condition |
| `FRA_corporate_stmicroelectronics_health` | 6 | STMicroelectronics condition |
| `FRA_corporate_orange_health` | 5 | France Télécom and Orange condition |
| `FRA_corporate_debt_pressure` | 2 | Corporate refinancing and balance-sheet stress |
| `FRA_corporate_chinese_vendor_dependency` | 0 | Reliance on Chinese telecom suppliers |

The source document's 0-100 variable changes are scaled by 0.1 for the first nine axes. Chinese vendor dependency is the sole gameplay exception because it models concentrated supplier lock-in and nonlinear replacement exposure rather than a literal source score: global sourcing adds 2, Nokia/Ericsson subtracts 1, Huawei adds 5, balanced multivendor subtracts 1, restrictive authorizations subtract 3, long-term Huawei authorization adds 2, and rapid diversification subtracts 4. That bounded matrix keeps the China-Connected Infrastructure outcome reachable at its dependency threshold of 7 without a repeatable policy.

Research proposals are mapped conservatively to the installed research-bonus system: 3-4% becomes one 5% use, 5-6% becomes one 10% use, and 7-8% becomes two 10% uses. The module adds no dynamic modifiers, repeatable policies, or new buildings.

## Capstone Priority

The outcome resolver evaluates in this order so overlapping states are deterministic:

1. **European Strategic Autonomy**: European integration at least 8, telecom capacity at least 7, semiconductor capacity at least 7, and Chinese vendor dependency no more than 4.
2. **French National Champions**: strategic sovereignty at least 8, telecom capacity at least 6, semiconductor capacity at least 6, and debt pressure no more than 5.
3. **China-Connected Infrastructure**: digital infrastructure at least 7 and Chinese vendor dependency at least 7.
4. **Globalized Technology Market**: strategic sovereignty no more than 4, digital infrastructure at least 7, Orange health at least 6, and STMicroelectronics health at least 6.
5. **Resilient Multivendor System**: fallback when none of the more specific profiles applies.

## Event Art Source Register

All tracked outputs are 217 by 163 pixels, legacy DDS with DXT5/BC3 compression, one mip level, and no tracked source original. Each output is a cropped, resized, color-adjusted derivative; the France Télécom logo is centered on a blue field. Source hashes identify the downloaded working copy, which is a Wikimedia preview where noted.

| Output | Source and attribution | License | Working-copy SHA-256 | Output SHA-256 |
| --- | --- | --- | --- | --- |
| `FRA_corporate_alcatel.dds` | [Alcatel-Lucent Boulogne](https://commons.wikimedia.org/wiki/File:Alcatel-Lucent_Boulogne.jpg), AnaBé, 2014 | CC BY-SA 3.0 | `7e5635e56a8942eda43fff779df8abd6e40162d77060a9724df92fef3e1461c8` | `c508eac7ab505c29783f7871ed7984cda99d874a7ff39a345f6f2826a6916a26` |
| `FRA_corporate_stmicroelectronics.dds` | [STMicroelectronics building](https://commons.wikimedia.org/wiki/File:STMicroelectronics-building.JPG), Alexey M., 2015 | CC BY-SA 4.0 | `9457493d7193729fd2f428955915c1389cb500a19aa3ac74606684aa20a683e5` | `4fabc5c7987a757b9617f8cda89c7386b19570500b51ddc2abe6e53fe3c31cca` |
| `FRA_corporate_cleanroom.dds` | [Clean room](https://commons.wikimedia.org/wiki/File:Clean_room.jpg), NASA Glenn Research Center, 2004 | Public domain, U.S. government | `df03be14959ff199b6b94223abab720a42791094549592c53f5ed823398bd298` | `426d7192fab0972f3595c5f3ce35be7941262621008ccc9e046beea899e01c05` |
| `FRA_corporate_wafer.dds` | [Silicon wafer](https://commons.wikimedia.org/wiki/File:Silicon_wafer.jpg), Inductiveload, 2010 | Public-domain dedication | `384d68bbd3e0e8acecd21d5b92f9a465633e4ec6fc9f3824455e3ad10e39224d` | `65c3762f02a93194daa04b40668a4652584bb3a2b99bcbd0ddb736f1ef8facf9` |
| `FRA_corporate_france_telecom.dds` | [France Télécom 1999 logo](https://commons.wikimedia.org/wiki/File:Logo_of_France_Telecom_(1999).svg), unknown author, 960-pixel PNG preview | Public-domain text logo | `d8e5574c8290fb3241bced1e0f641ec6337190d83b74893dad7ed82ae48cfe00` | `2d42444e24bd0b94667c436a9d1d6aecef33808a37c3363e708a6679062d7a7f` |
| `FRA_corporate_orange_labs.dds` | [Orange Labs Rennes](https://commons.wikimedia.org/wiki/File:Orange_Labs_Rennes.JPG), Sylenius, 1,280-pixel preview | CC BY-SA 3.0 | `49e394d75b00756e0bf80c1fe428640debf3cbfe84a1bddbb4c2563c2fc07dc0` | `3a42708b8911a6573c62d802d14460fd13c7ec299c61adfd805910e2de7bb198` |
| `FRA_corporate_fiber.dds` | [Fiber deployment in Lannion](https://commons.wikimedia.org/wiki/File:Pose_fibre_optique_Lannion_(18198103421).jpg), missbutterflies, 960-pixel preview, 2015 | CC BY-SA 2.0 | `bfb4580fc6f06e6b2d2bd8a0ba2e9b13301b2f906ed42c6a837ab1401bf2bc24` | `9270c3bb35edfa3f6b775a991b71287768e1b3102b1c475070b63b304556a2f1` |
| `FRA_corporate_5g.dds` | [Cellular 5G equipment](https://commons.wikimedia.org/wiki/File:Cellular_5G_Equipment_-_Cell_Tower_Antennas.jpg), Tony Webster, 1,280-pixel preview, 2019 | CC BY 2.0 | `11aa18f2985332b6906f1d09ad4177ef2bc95868025e9ccbd1ec3df6171fb098` | `946dec5e9c29a77d1641727e37dcd39ccd2575deb3b2190d7b84dda0b92b0d00` |

The derivatives are distributed under the repository's CC BY-SA 4.0 license. Attribution and compatible share-alike terms are retained here for each externally sourced work.

## Acceptance Boundary

Static acceptance requires the Corporate History contract and scenario fixtures to recognize France, all ten variables to initialize and clamp, every visible ID to have one scheduling owner, the hidden reconstruction path to be event-free, the dashboard keys to resolve, the English localisation file to contain every referenced key, and all eight sprites to resolve to valid DDS files. Static validation is not evidence of an in-game playthrough; console and natural-runtime checks remain separate acceptance tasks.
