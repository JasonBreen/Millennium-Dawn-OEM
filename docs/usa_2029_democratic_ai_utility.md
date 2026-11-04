# USA 2029 Democratic AI Reconstruction and Public Utility

This branch extends `USA_focus_2028_democrat_victory` in `common/national_focus/05_usa.txt`. That election focus retains its existing inauguration and ruling-party gate, `date > 2029.1.20` and `western_liberals_are_in_power = yes`. The new substantive focuses also require Western Liberal rule when chosen.

## Focus map

```
USA_focus_2028_democrat_victory
  AI Recovery and Resilience Act
    Monitor Systemic AI Risk -> No Blank Checks for AI Firms -> Conditional Reconstruction Finance
    Protect the Global Silicon Supply -> A Second Semiconductor Buildout -> Memory and Packaging Safeguards
    National Public AI Research Service -> A Grid for Intelligence -> Open-Weight Research Grants
  [all three final focuses required] -> The Intelligence Utility Act -> Unmetered Public AI Access
```

## Gameplay

* Twelve focuses with a combined one-time nominal treasury cost of **$203 billion** in Millennium Dawn treasury terms, spread over the branch.
* New permanent country ideas reward stability, chip availability, foundry construction/productivity, grid investment, open-weight research, and public inference accessibility. Their tradeoffs include administrative cost, consumer-goods burden, and the increased electricity/chip demand of public access.
* The Intelligence Utility Act requires all three completed branches: financing, memory, and open research. Separate `prerequisite` blocks enforce an AND gate.
* `USA_focus_public_compute_commons`, already part of the presidential agenda, is not duplicated. Completing it before the Utility Act gives a small one-time political-power synergy reward.
* This is deliberately **not** an AGI technology unlock, AI Race stage advance, guaranteed AI crash event, or literal infinite-compute resource. It represents unmetered ordinary use as a focus and national spirit.

## Integration boundaries

No new corporate-history events, AI Race effects, or new tech tiers. Existing UK/US factory systems and country-level microchip modifiers continue to own their underlying simulation. Focus icons use keys already referenced in the US focus tree. Idea illustrations use pictures already used by USA AI, semiconductor, and presidential agenda ideas.

## Verification boundaries

Authoring checks cover brace balance, unique focus, idea, and localization keys, parent references, focus coordinates, and preservation of the existing focus source. GitHub CI validates content on every PR head. HOI4 runtime/load testing and in-game focus-tree layout inspection remain manual.
