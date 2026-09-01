# Millennium Dawn OEM: Corporate & Industrial Roadmap

Status: Architectural Roadmap & Strategic Master Plan for Corporate Systems and Advanced Industry in MD OEM.

---

## 1. Executive Summary & Vision

The **Millennium Dawn OEM (Original Equipment Manufacturer)** framework models the modern era (2000–present) not merely through cabinet ministers and army divisions, but through the **technological, industrial, financial, and corporate foundations** that drive real-world geopolitical power.

Existing implementations have proven this architecture:
- **Tier 1 U.S. Corporate Systems & AI Industry Core** (`USA_ai_core`, `USA_oem` real-options economic layer).
- **National Corporate History Chains** (USA, CAN, CHI, FIN, FRA, GER, GBR, JAP, POL, RUS, SWE, TAI, UKR).
- **The Linux Ecosystem & Open Source Adapters** (`MD_linux_system`).
- **The Great AI Race Subsystem** (Phase 1 Architecture).

This roadmap outlines the next major horizons for the OEM corporate layer, expanding into critical supply-chain chokepoints, multilateral frontier tech competition, sovereign state capitalism, defense tech, clean energy, and bio-industrial power.

---

## 2. Core Architectural Principles

All new modules must strictly adhere to the established MD-OEM architectural standards:

1. **Strict Ownership Boundaries & Adapters**: Core systems (Energy, Microchips, Money, Tech trees, National focus trees) retain authoritative state. Corporate chains interact with external systems via documented read-only adapters, never raw duplicate writes.
2. **Deterministic & Bounded State Model**:
   - Country-level corporate variables use normalized integer scales: `0..10` (company/sector health) or `0..100` (macro indices).
   - Every mutating path must invoke clamping effects.
3. **Low-Frequency, Bounded Scheduling**:
   - No daily global polling.
   - Milestone scheduling runs on yearly dispatchers with monthly catch-up guards. Macro aggregations and ranking sweeps run quarterly or monthly.
4. **Three-Mode Runtime Contract**:
   - **Full**: Player-facing interactive events, decisions, GUI dashboards, and dynamic choices.
   - **Outcomes Only**: Reward-free, deterministic reconstruction for historical accuracy and AI-only games without popups.
   - **Off**: Complete deactivation without polluting variables, ideas, or base game mechanics.
5. **Idempotent Late-Start Reconstruction**:
   - Any save or bookmark (2000, 2017, 2026+) must reconstruct prior history without firing stale popups or double-counting bonuses.
6. **No Phantom Economies**:
   - Energy load, microchip consumption, and treasury flows must connect directly to MD's native energy calculation, microchip resource, and budget effects.

---

## 3. Thematic Roadmap Pillars

```
+-------------------------------------------------------------------------------+
|                       MD-OEM CORPORATE & INDUSTRIAL ROADMAP                   |
+-------------------------------------------------------------------------------+
| 1. Semiconductor Chokepoints (ASML, Samsung, SK Hynix, Rapidus)               |
| 2. The Great AI Race: Multilateral Expansion (China, Europe, Gulf States)    |
| 3. Critical Minerals, Gigafactories & EV Transition (Lithium, CATL, BYD)      |
| 4. Defense-Tech Revolution & Space Commercialization (Anduril, SpaceX)        |
| 5. Sovereign Wealth Funds & Geoeconomic Statecraft (PIF, Temasek, CFIUS)      |
| 6. Corporate Tax Arbitrage, Offshore Enclaves & FinTech (Ireland, OECD, CBDC) |
| 7. Biotech, mRNA & The Metabolic Economy (Novo Nordisk, BioNTech)             |
+-------------------------------------------------------------------------------+
```

---

### Pillar 1: Global Semiconductor & Lithography Chokepoints

While Taiwan (`TAI`) and the US (`USA`) are currently represented, the physical fabrication of advanced computing rests on three indispensable foreign pillars:

#### 1.1 Netherlands (`HOL`) — ASML & The Photolithography Monopoly
* **Core Concept**: 100% global monopoly on Extreme Ultraviolet (EUV) lithography systems required for sub-7nm fabrication.
* **Key Mechanics**:
  - **Technology Progression**: DUV immersion $\rightarrow$ EUV ($0.33\text{ NA}$) $\rightarrow$ High-NA EUV ($0.55\text{ NA}$).
  - **Supply Chain Triad**: Optical assemblies from Carl Zeiss (Germany), EUV light sources from Cymer (USA), and system integration in Veldhoven (Netherlands).
  - **Export Control Diplomacy**: Balancing Dutch strategic autonomy and bilateral trade with China against US export restrictions (Wassenaar Arrangement / ministerial export licensing).
* **State Variables (`0..10`)**:
  - `HOL_asml_lithography_leadership`: Dominance in next-generation scanner optics and wavelength control.
  - `HOL_asml_supply_chain_depth`: Integration with German optics and US light-source suppliers.
  - `HOL_asml_export_alignment`: Alignment with Western strategic export control regimes.

#### 1.2 South Korea (`KOR`) — The Chaebol Memory & Foundry Duopoly
* **Core Concept**: Samsung Electronics and SK Hynix control $>70\%$ of global DRAM/NAND and a near-monopoly on High-Bandwidth Memory (HBM3e/HBM4) for AI accelerators.
* **Key Mechanics**:
  - **SK Hynix HBM Leadership**: Dedicated silicon interposer packaging and memory stacking powering global AI accelerator stacks.
  - **Samsung Foundry Competition**: State-supported 3nm Gate-All-Around (GAA) foundry buildouts competing against TSMC.
  - **Chaebol Industrial Politics**: Balancing corporate dynasty governance, the Korean K-Chips Act, high domestic energy loads, and fab operations in mainland China (Wuxi/Xi'an).
* **State Variables (`0..10`)**:
  - `KOR_corporate_memory_dominance`: Global market share and technology lead in DRAM/HBM.
  - `KOR_corporate_foundry_competitiveness`: Leading-edge foundry yield rates and customer diversification.
  - `KOR_corporate_chaebol_alignment`: State-chaebol industrial coordination and domestic energy/site support.

#### 1.3 Japan (`JAP`) — Upstream Equipment, Materials & Rapidus
* **Core Concept**: Critical chemical and precision equipment monopolies (Tokyo Electron, Shin-Etsu silicon wafers, JSR photoresists) and the **Rapidus 2nm Consortium** (Hokkaido fab partnered with IBM).
* **Key Mechanics**:
  - Chemical and wafer export licensing tools.
  - State subsidies for Rapidus 2nm pilot lines and domestic semiconductor ecosystem restoration.

---

### Pillar 2: The Great AI Race — Multilateral Expansion (Phases 2 & 3)

Extending the global frontier race beyond the United States into major international hubs:

#### 2.1 China (`CHI`) — State-Coordinated Compute & Open Weights
* **Frontier Laboratories & Primes**: Huawei (Ascend 910 series / MindSpore), Baidu (Ernie), Alibaba (Qwen open-weights), Tencent, and frontier startups (DeepSeek, Moonshot, Zhipu AI).
* **Key Mechanics**:
  - **"East Data, West Compute" (东数西算)**: Mega data-center corridors in renewable/hydro-rich western provinces (Guizhou, Inner Mongolia, Ningxia).
  - **Architectural Efficiency under Sanctions**: Mixture-of-Experts (MoE), native FP8 precision, and algorithm distillation to overcome hardware compute bottlenecks.
  - **Civil-Military Intelligentization**: PLA doctrine integration and national AI compute pooling.

#### 2.2 Europe (`FRA` / `GBR` / `GER`) — Sovereign AI & The Brussels Effect
* **Frontier Laboratories**: Mistral AI (France), Google DeepMind (UK), Aleph Alpha (Germany), EuroHPC supercomputing network (LUMI, Leonardo, Jupiter).
* **Key Mechanics**:
  - **The Brussels Effect**: Balancing high regulatory compliance (EU AI Act) with open-source sovereignty.
  - **European Sovereign Compute**: Public-private GPU clouds and Franco-German industrial AI partnerships.

#### 2.3 Gulf States (`SAU` / `UAE`) — Sovereign Capital & Desert Compute
* **Entities**: G42 (UAE / Falcon models), MGX / Humat Al Mustaqbal, Saudi PIF.
* **Key Mechanics**:
  - Deploying sovereign wealth and massive nuclear/solar energy capacity to host hyperscale international AI clusters.

---

### Pillar 3: Critical Minerals, Battery Gigafactories & EV Transition

Modeling the physical raw materials and industrial base of the global energy transition:

#### 3.1 Critical Mineral Supply Chains & Export Quotas
* **Chokepoints**:
  - **Lithium**: South American Lithium Triangle (Chile, Bolivia, Argentina) vs. Australian hard-rock mining.
  - **Cobalt & Nickel**: DRC cobalt mining governance, Indonesian HPAL nickel refining dominance.
  - **Rare Earth Elements & Refining**: Chinese refining dominance in Gallium, Germanium, Graphite, and heavy rare earths; Western supply diversification initiatives (MP Materials, Lynas).

#### 3.2 Battery Gigafactories & Chemistry Evolution
* **Corporate Actors**: CATL (China), BYD (Blade Battery), LG Energy Solution (South Korea), Panasonic (Japan) vs. Northvolt (Europe) and Tesla 4680.
* **Technological Choices**: Low-cost LFP (Lithium Iron Phosphate) vs. High-Energy NMC/NCA vs. Next-Gen Solid-State Batteries.

#### 3.3 Legacy Automotive Disruption & Software Architecture
* **Corporate Transformation Chains**:
  - **Tesla**: Vertically integrated manufacturing, Gigafactories, autonomous driving (FSD / Robotaxi).
  - **BYD**: Extreme vertical integration from mining to microchips, driving down consumer EV cost curves.
  - **Toyota**: Hybrid vehicle hedge, solid-state battery R&D, resistance to pure BEV mandates.
  - **Volkswagen Group**: Dieselgate crisis recovery $\rightarrow$ CARIAD software struggles $\rightarrow$ MEB platform electrification.

---

### Pillar 4: Defense-Tech Revolution, Autonomy & Commercial Space

Modernizing military procurement from legacy cost-plus contracting to agile software-first defense primes:

#### 4.1 Silicon Valley Defense Tech & Autonomous Systems
* **Corporate Primes**: Anduril Industries (Lattice OS, autonomous interceptors, Ghost/Altius UAS), Skydio, Shield AI (Hivemind autonomy), Palantir AIP defense deployments.
* **Key Mechanics**:
  - Software-first procurement, attritable autonomous mass, and real-time sensor-to-shooter battle management networks.

#### 4.2 Commercial Space & Mega-Constellations
* **Corporate Actors**: SpaceX (Falcon 9 reusability, Starlink, Starship), Rocket Lab, Amazon Kuiper, Eutelsat/OneWeb.
* **Key Mechanics**:
  - **Orbital Bandwidth Hegemony**: Deploying proliferated LEO satellite constellations to boost communications and national cyber resilience.
  - **Dual-Use Spacecraft**: Military satcom (Starshield) and orbital rapid cargo deployment.

#### 4.3 International Defense Export Champions
* **Hanwha Aerospace / KAI** (South Korea): Rapid-delivery heavy armor and artillery (K9 Thunder) export diplomacy.
* **Baykar** (Turkey): Bayraktar TB2/Akinci drone export statecraft across Central Asia, Africa, and Eastern Europe.

---

### Pillar 5: Sovereign Wealth Funds & Geoeconomic Statecraft

State capitalism where national wealth funds act as instruments of foreign policy and strategic industrial transformation:

* **Sovereign Capital Allocators**:
  - **Saudi Arabia (PIF)**: Vision 2030, Neom giga-projects, international tech and infrastructure acquisitions.
  - **UAE (Mubadala / ADIA)**: Semiconductor investments (GlobalFoundries), aerospace, and global AI infrastructure.
  - **Singapore (Temasek & GIC)**: High-tech venture ecosystems and global logistics hubs.
  - **Norway (GPFG)**: World's largest sovereign fund; ESG ethical screening and global equity leverage.
  - **China (CIC & "Big Fund")**: National Integrated Circuit Industry Investment Fund financing domestic foundries and memory makers.
* **FDI Screening & Foreign Takeover Defense**:
  - CFIUS (USA) and EU Foreign Subsidies Regulation (FSR) mechanics to block hostile acquisitions of strategic tech firms or force divestments.

---

### Pillar 6: Corporate Tax Havens, Profit Shifting & Digital Currency

Connecting MD's treasury and corporate tax rates to multinational capital flows:

* **Offshore Financial Enclaves**:
  - Ireland (the "Double Irish" tech boom and EMEA corporate headquarters), Luxembourg, Switzerland, Singapore, Cayman Islands.
* **OECD Pillar 2 (15% Global Minimum Tax)**:
  - International treaty diplomacy establishing a global 15% corporate tax floor, triggering corporate relocation decisions and Digital Services Taxes (DSTs).
* **Private Stablecoins vs. Central Bank Digital Currencies (CBDCs)**:
  - Dollar-backed stablecoins (Tether USDT, Circle USDC) expanding US dollar liquidity globally vs. Sovereign CBDCs (China's e-CNY, Digital Euro).

---

### Pillar 7: Biotech, mRNA & The Metabolic Economy

Industrial-scale biotechnology driving macroeconomic growth and national crisis response:

* **mRNA & Rapid-Response Vaccines**:
  - BioNTech/Pfizer, Moderna, Oxford/AstraZeneca; advance market commitments (Operation Warp Speed) and pandemic industrial preparedness.
* **The Blockbuster Metabolic Economy**:
  - **Novo Nordisk (Denmark)**: GLP-1 (Ozempic/Wegovy) surge reshaping Danish GDP growth, trade balance, and currency appreciation.
  - **Eli Lilly (USA)**: Rival metabolic therapies and massive domestic manufacturing facility buildouts.

---

## 4. Implementation Phasing & Priority Matrix

| Phase | Module / Chain | Scope & Dependencies | Priority |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **Netherlands: ASML Lithography** | `HOL` chain: DUV/EUV progression, Zeiss/Cymer supply links, export controls | **Immediate (Tier 1)** |
| **Phase 1** | **South Korea: Samsung & SK Hynix** | `KOR` chain: Memory dominance, HBM packaging, 3nm foundry, Chaebol dashboard | **Immediate (Tier 1)** |
| **Phase 2** | **Great AI Race: China & Europe** | `CHI` & `FRA`/`GBR`/`GER` adapters for AI Race: Huawei, Baidu, Mistral, EuroHPC | **High (Tier 1/2)** |
| **Phase 2** | **Japan: Rapidus & Materials** | `JAP` chain update: Tokyo Electron, photoresist controls, Rapidus 2nm project | **High (Tier 2)** |
| **Phase 3** | **Critical Minerals & Battery Gigafactories** | Global resource layer: Lithium/Cobalt/Rare Earths, CATL, BYD, Tesla, Northvolt | **Medium (Tier 2)** |
| **Phase 3** | **Defense-Tech & Space Expansion** | `USA`/`TUR`/`KOR` chains: Anduril, SpaceX/Starlink, Baykar, Hanwha Aerospace | **Medium (Tier 2)** |
| **Phase 4** | **Sovereign Wealth Funds & Capital** | `SAU`/`UAE`/`SGP`/`NOR` dashboards: PIF, Mubadala, Temasek, FDI screening | **Strategic (Tier 3)** |
| **Phase 4** | **Tax Havens, OECD Pillar 2 & FinTech** | `IRE`/Global mechanics: Tax arbitrage, 15% minimum tax treaties, stablecoins | **Strategic (Tier 3)** |
| **Phase 4** | **Biotech & Metabolic Economy** | `DEN`/`USA` chains: Novo Nordisk macro shock, mRNA vaccine industrial base | **Flavor/Macro (Tier 3)** |

---

## 5. Standard Verification & Test Schema

Every new module added under this roadmap must satisfy:

1. **State Bounds**: All country variables initialize within declared bounds and clamp after every mutation path.
2. **Reconstruction Parity**: Late-start reconstruction (2000, 2017, 2026) reproduces correct historical state without orphaned ideas, duplicate flags, or unhandled dates.
3. **Three-Mode Integrity**: Full mode shows events/decisions; Outcomes Only resolves silently without popup spam; Off cleanly bypasses the chain with zero game impact.
4. **Energy & Economy Safety**: No phantom generation, direct writes to calculated energy variables, or un-guarded treasury deductions during bankruptcy states.
5. **Contract Validation**: Registered in `tools/corporate_history_contract.json` and covered by automated regression tests in `tools/tests/`.
