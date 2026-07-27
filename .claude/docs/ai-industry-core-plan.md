# United States AI Industry Core Architecture

## Scope

This is the pre-implementation contract for a Tier 1 United States AI industry chain. It defines ownership, state, chronology, integration, and validation before any events or effects are added.

The chain models the industrial system around artificial intelligence. It does not retell the histories of Microsoft, Google, Oracle, NVIDIA, TSMC, Micron, IBM, Apple, OpenAI, or Anthropic. Those owners retain their company milestones and state.

Reserved identifiers:

- Event namespace: `USA_ai_core_events`
- Root prefix: `USA_ai_core`
- Owning country: `USA`
- Visible events: `USA_ai_core_events.1` through `USA_ai_core_events.12`
- Hidden reconstruction event: `USA_ai_core_events.90`
- Completion marker: `USA_ai_core_capstone_resolved`

The `USA_ai_core` root avoids the live `USA_ai_defense_stack_review_board` identifier and separates the sector model from the existing military AI sequence in `events/United States.txt`.

## Industrial model

The chain represents one connected production system:

| Layer                  | Representation                                                                                         | Ownership boundary                                                                                                            |
| ---------------------- | ------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| Frontier laboratories  | Research-to-deployment capability and the availability of advanced models                              | AI Core tracks sector capacity; future OpenAI and Anthropic satellites own company formation, models, governance, and capital |
| Cloud providers        | Large-scale training and inference capacity, procurement access, and platform concentration            | Microsoft, Google, and Oracle retain company strategy; AI Core reads exact outcomes                                           |
| Accelerators           | Availability of high-end compute and exposure to export controls                                       | NVIDIA retains product and market choices                                                                                     |
| Foundries              | Access to leading-edge fabrication                                                                     | TSMC retains capacity and allocation choices                                                                                  |
| Advanced packaging     | Ability to turn dies and memory into deployable systems                                                | TSMC retains its packaging state                                                                                              |
| Memory                 | High-bandwidth-memory availability and domestic supply commitments                                     | Micron retains its HBM and fabrication state                                                                                  |
| Data centers           | Sector deployment depth and the infrastructure burden created by construction                          | AI Core owns the aggregate burden, not individual facilities                                                                  |
| Electricity            | Whether national generation can support new load without shortages or rate shocks                      | The existing energy system owns production, consumption, and balance                                                          |
| Government procurement | The federal government's ability to buy, evaluate, and govern AI systems                               | Existing Palantir and defense-procurement content owns program choices; AI Core reads exact outcomes                          |
| Export controls        | The tradeoff between frontier protection, allied supply, and market access                             | Company chains own compliance choices; AI Core owns the sector policy consequence                                             |
| Capital                | Whether frontier capability can be financed without leaving infrastructure or public legitimacy behind | AI Core owns the aggregate capital-allocation consequence                                                                     |
| Workforce legitimacy   | Labor consent, public trust, safety credibility, and political permission to expand                    | AI Core owns the sector-level measure and reads company-specific legitimacy state                                             |

No AI Core effect may write another chain's variable or flag. Ordinary technologies, including `artificial_intelligence_1` through `artificial_intelligence_14`, remain independent of Corporate History.

## State model

All six persistent variables are integers clamped to `0..10`.

| Variable                            | Initial value in 2000 | Definition                                                                                         |
| ----------------------------------- | --------------------: | -------------------------------------------------------------------------------------------------- |
| `USA_ai_core_frontier_capability`   |                     2 | Ability to train, evaluate, and deploy frontier systems                                            |
| `USA_ai_core_compute_depth`         |                     3 | Breadth and resilience of cloud, accelerator, foundry, packaging, memory, and data-center capacity |
| `USA_ai_core_ecosystem_openness`    |                     6 | Access to models, standards, research, and interoperable platforms                                 |
| `USA_ai_core_state_alignment`       |                     2 | Coordination between the sector and federal research, procurement, security, and industrial policy |
| `USA_ai_core_infrastructure_burden` |                     1 | Grid, water, permitting, financing, and regional costs imposed by AI infrastructure                |
| `USA_ai_core_public_legitimacy`     |                     5 | Workforce consent and public confidence in deployment, safety, and accountability                  |

Required owner effects:

- `USA_ai_core_initialize_state`
- `USA_ai_core_clamp_state`
- `USA_ai_core_reconstruct_history`
- `USA_ai_core_schedule_current_year_events`
- `USA_ai_core_resolve_capstone`
- `USA_ai_core_sync_openai_state`
- `USA_ai_core_sync_anthropic_state`

Required lifecycle flags:

- `USA_ai_core_state_initialized`
- `USA_ai_core_reconstruct_complete`
- `USA_ai_core_start_year_events_scheduled`
- `USA_ai_core_capstone_resolved`
- `USA_ai_core_openai_state_received`
- `USA_ai_core_anthropic_state_received`

The initialize, reconstruct, schedule, capstone, and satellite-receiver effects must be idempotent.

## Event spine

Dates are scheduler dates, expressed as the number of days after 1 January in parentheses. Historical-composite events use a documented policy or industrial milestone as the timing anchor without assigning the entire sector transition to one company.

### 1. The Post-Dot-Com Research Base

- Date: 29 January 2001 (`days = 28`)
- Status: Historical composite
- Industrial problem: Private capital and infrastructure investment contract after the internet boom, while public computing research remains fragmented.
- Government mechanism: Federal research funding, shared research infrastructure, and open publication requirements.
- Choices:
  - Protect open research and patient public funding.
  - Concentrate funds in mission-oriented federal programs.
  - Let private capital reallocate the sector.
- Variables: openness, state alignment, public legitimacy, and frontier capability
- External reads: none; this establishes the sector baseline
- Later consequence: Determines whether the 2012 learning breakthrough enters an open research ecosystem or a concentrated procurement system.

### 2. Utility Computing Becomes Industrial Capacity

- Date: 14 March 2006 (`days = 72`)
- Status: Historical composite, anchored to the public launch of Amazon S3
- Industrial problem: On-demand computing lowers entry barriers but begins concentrating infrastructure in hyperscale providers.
- Government mechanism: Federal cloud procurement standards, interoperability requirements, and small-firm access.
- Choices:
  - Use procurement to accelerate utility computing.
  - Require portable and open cloud interfaces.
  - Preserve incumbent contracting and security controls.
- Variables: compute depth, ecosystem openness, state alignment, and infrastructure burden
- External reads: none; later company outcomes must not rewrite a 2006 reconstruction choice
- Later consequence: Modifies the speed and concentration of the 2012 and 2019 compute expansions.

### 3. Deep Learning Becomes a Compute Industry

- Date: 3 December 2012 (`days = 337`)
- Status: Historical composite, anchored to the 2012 ImageNet paper and conference
- Industrial problem: Research performance becomes dependent on data, accelerators, and scalable compute.
- Government mechanism: Research-compute grants, shared datasets, and university access to accelerators.
- Choices:
  - Fund shared national research compute.
  - Back private accelerator and cloud scaling.
  - Prioritize accountable datasets and workforce consent.
- Variables: frontier capability, compute depth, ecosystem openness, and public legitimacy
- External reads: `USA_gpu_2012_alexnet_open_research` and `USA_gpu_2012_alexnet_commercialization`
- Later consequence: Establishes the capability base used by the 2017 frontier shift.

### 4. A Federal AI Research Strategy

- Date: 12 October 2016 (`days = 285`)
- Status: Historical, anchored to the National AI Research and Development Strategic Plan
- Industrial problem: Federal programs lack a common research, workforce, safety, and evaluation agenda.
- Government mechanism: Coordinated research priorities, test infrastructure, standards, and workforce programs.
- Choices:
  - Build an open civilian research program.
  - Align research with federal missions and procurement.
  - Center safety, labor transition, and public accountability.
- Variables: state alignment, ecosystem openness, frontier capability, and public legitimacy
- External reads: `USA_ibm_watson_enterprise`
- Later consequence: Shapes the policy response to the 2017 architecture shift and the 2019 initiative.

### 5. The Transformer and the Frontier Shift

- Date: 12 June 2017 (`days = 162`)
- Status: Historical, anchored to the first public version of "Attention Is All You Need"
- Industrial problem: Model scaling increases the value of compute, data, and broadly reusable architectures.
- Government mechanism: Open-science conditions, frontier evaluation funding, and compute-access programs.
- Choices:
  - Preserve open publication and broad research access.
  - Build a protected frontier research consortium.
  - Leave scaling to vertically integrated platforms.
- Variables: frontier capability, ecosystem openness, compute depth, and infrastructure burden
- External reads: `USA_google_infrastructure_depth`, `USA_google_workforce_consent`, `USA_gpu_2017_volta_broad_access`, and `USA_gpu_2017_volta_full_stack`
- Later consequence: Determines whether later foundation-model capacity is open, state-aligned, or platform-concentrated.

### 6. The American AI Initiative

- Date: 11 February 2019 (`days = 41`)
- Status: Historical, anchored to Executive Order 13859
- Industrial problem: Research leadership, standards, data access, and workforce policy are divided across agencies.
- Government mechanism: Coordinated federal research, standards, regulatory guidance, and access to federal data and computing resources.
- Choices:
  - Coordinate agencies around civilian innovation.
  - Tie the initiative to strategic competition.
  - Use standards and oversight to earn public consent.
- Variables: state alignment, frontier capability, ecosystem openness, and public legitimacy
- External reads: none; the existing defense AI choice is a later 2024 milestone
- Later consequence: Sets the federal posture inherited by the 2020 research-institute buildout.

### 7. National Research Compute at Scale

- Date: 26 August 2020 (`days = 238`)
- Status: Historical composite, anchored to the National AI Research Institutes program
- Industrial problem: Foundation-scale research requires durable compute, interdisciplinary institutions, and a skilled workforce.
- Government mechanism: Federally supported research institutes, public-private compute access, and workforce funding.
- Choices:
  - Build a distributed public research network.
  - Use cloud partnerships to scale quickly.
  - Concentrate resources in national-security missions.
- Variables: compute depth, frontier capability, state alignment, ecosystem openness, and public legitimacy
- External reads: `USA_oracle_cloud_public_sector`, `USA_ibm_federal_systems_arm`, `USA_microsoft_cloud_cross_platform`, and `USA_microsoft_cloud_hybrid`
- Later consequence: Determines how much public capacity exists before generative commercialization.

### 8. Trust Before Mass Commercialization

- Date: 4 October 2022 (`days = 276`)
- Status: Historical, anchored to the Blueprint for an AI Bill of Rights
- Industrial problem: Rapid commercial deployment outpaces safeguards, worker consent, and public accountability.
- Government mechanism: Rights-based procurement guidance, impact testing, notice, human alternatives, and sector oversight.
- Choices:
  - Make rights protections a federal procurement floor.
  - Prefer voluntary industry assurance.
  - Accelerate deployment and address harms afterward.
- Variables: public legitimacy, state alignment, frontier capability, and ecosystem openness
- External reads: `USA_google_workforce_consent`, `USA_gpu_2022_hopper_broad_access`, and `USA_gpu_2022_hopper_full_stack`
- Later consequence: Alters the legitimacy cost and regulatory strength of the 2023 federal response.

### 9. Procurement, Evaluation, and Export Control

- Date: 30 October 2023 (`days = 302`)
- Status: Historical composite, anchored to Executive Order 14110 and the October 2023 advanced-computing controls
- Industrial problem: The federal government must buy and evaluate capable systems while protecting advanced compute supply.
- Government mechanism: Model reporting, testing standards, procurement rules, export controls, and agency capacity.
- Choices:
  - Build a federal evaluation and procurement capability.
  - Prioritize strategic controls and trusted suppliers.
  - Preserve commercial speed with targeted reporting.
- Variables: state alignment, frontier capability, compute depth, ecosystem openness, and public legitimacy
- External reads: `USA_nvidia_export_control_lobby`, `USA_palantir_model_expanded`, `USA_palantir_public_oversight`, `USA_ibm_federal_systems_arm`, `TAI_tsmc_export_control_compliance`, and `TAI_tsmc_export_control_defiance`
- Later consequence: Controls the supply and legitimacy tradeoffs applied in 2024.

### 10. The HBM, Packaging, and Power Squeeze

- Date: 20 December 2024 (`days = 354`)
- Status: Historical composite, anchored to the December 2024 HBM controls and Department of Energy data-center demand assessment
- Industrial problem: Frontier expansion is constrained by HBM, advanced packaging, leading-edge fabrication, data-center sites, and electricity.
- Government mechanism: Supply-chain finance, allied coordination, grid planning, permitting, and ratepayer protection.
- Choices:
  - Finance a resilient domestic and allied compute stack.
  - Prioritize frontier clusters and strategic allocation.
  - Pace expansion to grid and community capacity.
- Variables: compute depth, infrastructure burden, state alignment, public legitimacy, and frontier capability
- External reads: `USA_micron_hbm_position`, `USA_micron_us_fab_commitment`, `TAI_tsmc_advanced_packaging_expanded`, `USA_nvidia_h100_capacity_partnership`, `USA_gpu_2024_national_buildout`, `USA_gpu_2024_open_buildout`, `USA_stack_ti_foundational_viable`, `USA_stack_micron_memory_viable`, `energy_balance`, `unfulfilled_energy_demand_var`, and `energy_difference_variable`
- Later consequence: Determines the cost and feasibility of the 2025 buildout.

### 11. The National Compute Buildout

- Date: 23 July 2025 (`days = 203`)
- Status: Historical, anchored to America's AI Action Plan and the federal data-center permitting order
- Industrial problem: National-scale compute expansion collides with permitting, power, finance, supply-chain, and regional legitimacy constraints.
- Government mechanism: Permitting coordination, infrastructure finance, federal land and procurement, transmission planning, and allied supply agreements.
- Choices:
  - Build fast through nationally coordinated infrastructure.
  - Condition support on grid and community investment.
  - Rely on private clusters and market allocation.
- Variables: compute depth, infrastructure burden, state alignment, public legitimacy, and ecosystem openness
- External reads: all exact compute-supply and energy reads listed for event 10, plus `USA_apple_silicon_autonomy`, `USA_apple_private_cloud_compute`, and `USA_apple_on_device_ai`
- Later consequence: Sets the final capstone eligibility and the burden inherited by 2026.

### 12. Who Pays for the Frontier?

- Date: 4 March 2026 (`days = 62`)
- Status: Historical policy anchor with alternate-history outcomes, anchored to the Ratepayer Protection Pledge
- Industrial problem: Frontier leadership is no longer separable from electricity prices, infrastructure finance, market structure, and public permission.
- Government mechanism: Ratepayer protections, private generation commitments, federal procurement, open research infrastructure, and resilience investment.
- Choices and terminal outcomes:
  - Private frontier leadership: `USA_ai_core_private_frontier_primacy`
  - Open research and interoperable platforms: `USA_ai_core_open_innovation_ecosystem`
  - A federal compute and procurement compact: `USA_ai_core_federal_compute_compact`
  - A resilient domestic and allied industrial stack: `USA_ai_core_resilient_industrial_base`
  - Leadership constrained by unresolved power burden: `USA_ai_core_power_constrained_leadership`
- Variables: all six variables are evaluated; no variable changes occur after terminal resolution
- External reads: all contract reads are optional weights, never hard reachability gates
- Later consequence: Applies exactly one persistent outcome idea and sets `USA_ai_core_capstone_resolved`

## Cross-chain API

All reads are optional context, AI-weight, or capstone inputs. Missing or unresolved company state must fall back to AI Core variables and must never block event reachability.

Reconstruction may consume an external outcome only when that outcome's canonical milestone is not later than the AI Core milestone being reconstructed. Later owner state must not flow backward into an earlier historical choice.

| AI Core read                             | Owning chain                   | Context             | Why needed                                               |
| ---------------------------------------- | ------------------------------ | ------------------- | -------------------------------------------------------- |
| `USA_microsoft_cloud_cross_platform`     | Microsoft                      | 2020, capstone      | Signals interoperable cloud depth                        |
| `USA_microsoft_cloud_hybrid`             | Microsoft                      | 2020, capstone      | Signals mixed public-private compute capacity            |
| `USA_microsoft_openai_aligned`           | Microsoft                      | Late 2023 onward    | Signals concentrated frontier alignment                  |
| `USA_microsoft_openai_diversified`       | Microsoft                      | Late 2023 onward    | Signals diversified compute and capital                  |
| `USA_microsoft_openai_regulated`         | Microsoft                      | Late 2023 onward    | Signals state oversight of frontier partnership          |
| `USA_google_infrastructure_depth`        | Google                         | 2017 onward         | Measures hyperscale infrastructure depth                 |
| `USA_google_workforce_consent`           | Google                         | 2017 onward         | Supplies a company-level workforce legitimacy signal     |
| `USA_oracle_cloud_public_sector`         | Oracle                         | 2020 onward         | Signals public-sector cloud procurement capacity         |
| `USA_nvidia_h100_capacity_partnership`   | NVIDIA                         | 2024 onward         | Signals shared accelerator-capacity strategy             |
| `USA_nvidia_export_control_lobby`        | NVIDIA                         | 2023 onward         | Signals pressure against strict strategic controls       |
| `TAI_tsmc_export_control_compliance`     | TSMC                           | 2023 onward         | Signals compliance with strategic controls               |
| `TAI_tsmc_export_control_defiance`       | TSMC                           | 2023 onward         | Signals resistance to strategic controls                 |
| `TAI_tsmc_advanced_packaging_expanded`   | TSMC                           | 2024 onward         | Signals availability of advanced packaging               |
| `USA_micron_hbm_position`                | Micron                         | 2024 onward         | Measures domestic HBM position                           |
| `USA_micron_us_fab_commitment`           | Micron                         | 2024 onward         | Measures domestic fabrication commitment                 |
| `USA_ibm_watson_enterprise`              | IBM                            | 2016 onward         | Signals enterprise AI adoption                           |
| `USA_ibm_watsonx_open`                   | IBM                            | 2023 onward         | Signals open model and platform strategy                 |
| `USA_ibm_watsonx_services`               | IBM                            | 2023 onward         | Signals service-led deployment                           |
| `USA_ibm_watsonx_regulated`              | IBM                            | 2023 onward         | Signals regulated enterprise deployment                  |
| `USA_ibm_federal_systems_arm`            | IBM                            | 2020 onward         | Signals federal systems and procurement capacity         |
| `USA_apple_silicon_autonomy`             | Apple                          | 2025 onward         | Measures vertically integrated compute autonomy          |
| `USA_apple_private_cloud_compute`        | Apple                          | 2025 onward         | Signals privacy-oriented cloud compute                   |
| `USA_apple_on_device_ai`                 | Apple                          | 2025 onward         | Signals distributed, lower-infrastructure inference      |
| `USA_gpu_2012_alexnet_open_research`     | GPU development                | 2012 reconstruction | Signals open diffusion of the deep-learning breakthrough |
| `USA_gpu_2012_alexnet_commercialization` | GPU development                | 2012 reconstruction | Signals concentrated commercialization                   |
| `USA_gpu_2017_volta_broad_access`        | GPU development                | 2017 onward         | Signals broad access to accelerator capacity             |
| `USA_gpu_2017_volta_full_stack`          | GPU development                | 2017 onward         | Signals vertically integrated accelerator deployment     |
| `USA_gpu_2020_shortage_capacity`         | GPU development                | 2020 onward         | Signals capacity-first shortage response                 |
| `USA_gpu_2020_shortage_coordination`     | GPU development                | 2020 onward         | Signals coordinated allocation during shortage           |
| `USA_gpu_2022_hopper_broad_access`       | GPU development                | 2022 onward         | Signals broad access to frontier accelerators            |
| `USA_gpu_2022_hopper_full_stack`         | GPU development                | 2022 onward         | Signals full-stack accelerator concentration             |
| `USA_gpu_2024_national_buildout`         | GPU development                | 2024 onward         | Signals national-scale compute expansion                 |
| `USA_gpu_2024_open_buildout`             | GPU development                | 2024 onward         | Signals open-access compute expansion                    |
| `USA_stack_ti_foundational_viable`       | Texas Instruments              | 2024 onward         | Signals a viable domestic foundational-chip layer        |
| `USA_stack_micron_memory_viable`         | Micron                         | 2024 onward         | Signals a viable domestic memory layer                   |
| `USA_accelerated_ai_defense_stack`       | United States national content | 2024 onward         | Signals accelerated defense integration                  |
| `USA_ai_defense_stack_review_board`      | United States national content | 2024 onward         | Signals review-board governance                          |
| `USA_palantir_model_expanded`            | Palantir sequence              | 2023 onward         | Signals expanded government-data deployment              |
| `USA_palantir_public_oversight`          | Palantir sequence              | 2023 onward         | Signals public oversight of government-data systems      |
| `energy_balance`                         | Energy system                  | 2024 onward         | Detects aggregate surplus or shortage                    |
| `unfulfilled_energy_demand_var`          | Energy system                  | 2024 onward         | Detects unmet demand                                     |
| `energy_difference_variable`             | Energy system                  | 2024 onward         | Measures absolute production-consumption difference      |

`TAI_tsmc_advanced_packaging_expanded` must be read only inside an existence-guarded `TAI` scope. AI Core must not create fallback TSMC state.

No existing owner needs a new write into AI Core. The future OpenAI and Anthropic chains are the only planned callback users:

- Their terminal owner effects may call `USA_ai_core_sync_openai_state` or `USA_ai_core_sync_anthropic_state`.
- Those receiver effects are owned by AI Core, read an exact satellite terminal state, adjust only AI Core variables, set the matching receipt flag, clamp state, and then become no-ops.
- Satellite code never uses `set_variable`, `add_to_variable`, `set_country_flag`, or `clr_country_flag` on an `USA_ai_core` identifier.

## OpenAI and Anthropic satellites

### AI Core owns

- Sector-wide capability, compute, openness, state alignment, infrastructure burden, and legitimacy
- Federal research, procurement, evaluation, export-control, and infrastructure policy
- Supply-chain aggregation across accelerators, foundries, packaging, memory, data centers, and electricity
- The five national industry outcomes

### OpenAI owns

- Laboratory formation and mission
- Company governance and control
- Model and product milestones
- Capital formation and non-Microsoft compute relationships
- Company safety and commercialization choices

Microsoft continues to own the existing OpenAI partnership milestone and the exact `USA_microsoft_openai_*` outcomes. The OpenAI satellite must read that state rather than replaying the partnership.

### Anthropic owns

- Company formation and public-benefit governance
- Model, safety-case, and deployment milestones
- Cloud-capital relationships
- Company-specific safety, access, and commercialization choices

Neither satellite gets its own national compute, export-control, electricity, or federal-procurement event. Those are AI Core milestones. AI Core may mention company behavior only as sector context and must not set company outcomes.

## Game-rule semantics

### Full

- Initialize the state in the Tier 1 startup dispatcher.
- Reconstruct every milestone before the start date through hidden effects.
- Queue only milestones in the current year.
- Continue yearly scheduling after startup.
- Show all unresolved visible events.
- Resolve the capstone once its date and prerequisites are reached.

### Outcomes Only

- Initialize and reconstruct state without visible historical events.
- Resolve historical choices through deterministic, weighted hidden effects.
- Apply exactly one terminal outcome when the capstone date is reached or already passed.
- Preserve the same variable bounds, external-read fallbacks, and completion marker as Full.

### Off

- Do not initialize AI Core state.
- Do not queue AI Core events.
- Do not add AI Core ideas or outcomes.
- Do not alter ordinary AI technologies, national focuses, research categories, Palantir content, energy calculations, or company chains.

### Late-start reconstruction

`USA_ai_core_reconstruct_history` applies milestones whose canonical dates are earlier than the start date in chronological order. It must not fire visible events, spend treasury, grant temporary modifiers, schedule delayed events, or write external state.

After reconstruction:

1. Clamp all six variables.
2. Set `USA_ai_core_reconstruct_complete`.
3. Schedule only still-unresolved milestones in the current year.
4. Resolve the capstone silently if its date is already past.

### Completion

`USA_ai_core_capstone_resolved` is the sole completion marker. Exactly one of the five outcome ideas may exist. Startup, yearly, monthly catch-up, and satellite callbacks must all become no-ops after completion.

## Energy interface

The existing energy calculation in `common/scripted_effects/!_energy_effects.txt` owns:

- `energy_balance`
- `energy_balance_value_display`
- `unfulfilled_energy_demand_var`
- `energy_difference_variable`
- Production, consumption, load sharing, and deficit alerts

AI Core may read `energy_balance`, `unfulfilled_energy_demand_var`, and `energy_difference_variable` after the normal energy calculation. It must never set, add to, clamp, or clear them.

Implementation should represent data-center burden through AI Core state and, if a gameplay modifier is required, an AI Core-owned low, elevated, or critical load idea using an existing validated energy-use modifier. It must not:

- Create a second electricity currency or balance
- Treat `internet_station` as a data-center building
- Directly overwrite calculated energy variables
- Add national power generation without an explicit player choice and visible cost
- Make Corporate History Off change the ordinary energy economy

## Validation design

### Contract entry

Add one entry to `tools/corporate_history_contract.json` only during implementation:

- `name`: `AI Industry Core`
- `tag`: `USA`
- `namespace`: `USA_ai_core_events`
- `root`: `USA_ai_core`
- `tier`: `1`
- `owned_prefixes`: exactly `USA_ai_core`
- `variables`: the six variables and `0..10` bounds above
- `outcome_idea_prefixes`: exactly `USA_ai_core_`
- `requires_current_year_scheduler`: `true`
- `allow_yearly_scheduler_duplicates`: `true`
- `allowed_reads`: exactly the Cross-chain API identifiers
- `allowed_writes`: empty

### Required tests

Extend `tools/validation/tests/validate_corporate_history_contract_test.py` with fixtures that prove:

- All six variables initialize before any read and are clamped after every mutation path.
- No AI Core script writes an identifier outside `USA_ai_core`.
- Every cross-chain read is exact and appears in `allowed_reads`.
- The guarded TSMC read does not require TSMC state to exist.
- Full, Outcomes Only, and Off each follow their documented lifecycle.
- Outcomes Only and late-start reconstruction fire no visible event.
- Off leaves `artificial_intelligence_1` through `artificial_intelligence_14` and unrelated national content untouched.
- Exactly one capstone outcome is applied.
- Both satellite receiver effects are idempotent.
- Energy variables are read-only from AI Core files.

### Scheduler ownership

- Tier 1 startup owns initialization, reconstruction, and the first current-year schedule.
- The United States yearly dispatcher owns the normal yearly call.
- A bounded monthly catch-up may call only `USA_ai_core_schedule_current_year_events`.
- Each visible event has its own scheduled and resolved guard.
- The validator must reject callerless scheduler anchors and duplicate unguarded callers.

### Reconstruction

- Reconstruction processes milestones in canonical order.
- It never schedules a past visible event.
- It does not require another corporate chain to be initialized.
- All external reads have a neutral fallback.
- A 2000, mid-chain, 2026, and post-2026 start each produce a bounded, completed state.

### Clamps

- `USA_ai_core_clamp_state` clamps all six variables to `0..10`.
- Every visible option, reconstruction path, Outcomes Only path, and satellite receiver calls the clamp effect after mutation.
- No direct event-local clamp may replace the owner effect.

## Implementation file map

The later implementation task may touch only the files required by this map:

| Purpose                                                           | File                                                                 |
| ----------------------------------------------------------------- | -------------------------------------------------------------------- |
| Visible and hidden events                                         | `events/USA_ai_core_events.txt`                                      |
| State, reconstruction, scheduling, receiver effects, and capstone | `common/scripted_effects/USA_ai_core_effects.txt`                    |
| Persistent and infrastructure-load ideas                          | `common/ideas/USA_ai_core_ideas.txt`                                 |
| Tier 1 startup, yearly, and bounded catch-up wiring               | `common/scripted_effects/00_corporate_history_dispatch_effects.txt`  |
| Framework startup and rule semantics                              | `common/scripted_effects/00_corporate_history_effects.txt`           |
| English localisation                                              | `localisation/english/MD_focus_USA_l_english.yml`                    |
| Game-rule text, only if semantics change                          | `localisation/english/MD_game_rules_l_english.yml`                   |
| Validation contract                                               | `tools/corporate_history_contract.json`                              |
| Contract regressions                                              | `tools/validation/tests/validate_corporate_history_contract_test.py` |
| Player-facing release note                                        | `Changelog.txt`                                                      |

No art, non-English localisation, resources, technology, focus-tree, or company-chain file is part of the initial implementation.

## Source register

Implementation prose must be checked against primary sources:

- [Amazon S3 launch, 14 March 2006](https://aws.amazon.com/blogs/aws/amazon_s3/)
- [AlexNet, Advances in Neural Information Processing Systems 25](https://proceedings.neurips.cc/paper_files/paper/2012/hash/c399862d3b9d6b76c8436e924a68c45b-Abstract.html)
- [National AI Research and Development Strategic Plan, October 2016](https://www.nitrd.gov/pubs/national_ai_rd_strategic_plan.pdf)
- ["Attention Is All You Need," first submitted 12 June 2017](https://arxiv.org/abs/1706.03762)
- [Executive Order 13859, 11 February 2019](https://www.govinfo.gov/link/cpd/executiveorder/13859)
- [National AI Research Institutes, launched in 2020](https://www.nsf.gov/focus-areas/ai/institutes)
- [Blueprint for an AI Bill of Rights, October 2022](https://bidenwhitehouse.archives.gov/ostp/ai-bill-of-rights/)
- [Executive Order 14110, 30 October 2023](https://www.govinfo.gov/app/details/DCPD-202300949)
- [Commerce Department advanced-computing controls, October 2023](https://www.bis.gov/press-release/commerce-strengthens-restrictions-advanced-computing-semiconductors-semiconductor-manufacturing-equipment)
- [Commerce Department HBM and semiconductor controls, December 2024](https://www.bis.gov/press-release/commerce-strengthens-export-controls-restrict-chinas-capability-produce-advanced-semiconductors-military)
- [Department of Energy data-center electricity-demand assessment, December 2024](https://www.energy.gov/articles/doe-releases-new-report-evaluating-increase-electricity-demand-data-centers)
- [America's AI Action Plan, July 2025](https://www.whitehouse.gov/wp-content/uploads/2025/07/Americas-AI-Action-Plan.pdf?inline=1)
- [Federal data-center permitting order, 23 July 2025](https://www.whitehouse.gov/presidential-actions/2025/07/accelerating-federal-permitting-of-data-center-infrastructure/)
- [Ratepayer Protection Pledge, March 2026](https://www.whitehouse.gov/fact-sheets/2026/03/fact-sheet-president-donald-j-trump-advances-energy-affordability-with-the-ratepayer-protection-pledge/)

The 2001 event is deliberately a historical composite. Before implementation, its description must be grounded in contemporaneous federal research-budget and labor-market sources rather than assigning the post-dot-com adjustment to a single announcement.
