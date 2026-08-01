# CI results — Copilot third-pass

Integration head: `556b403bca6ecb408d9af9f492a521325ee8a79f`

## CI at current main

| Workflow | Run ID | SHA | Status |
| --- | --- | --- | --- |
| Pylint | 30705408493 | 556b403b | ✅ success |
| Validator Cache (main) | 30705408471 | 556b403b | ✅ success |

## Local validator runs (this pass, on 556b403b)

| Validator | Result | Notes |
| --- | --- | --- |
| `validate_events.py` | 727 warnings | All pre-existing upstream (`czech_skoda.2` missing loc keys, etc.); zero OEM-specific findings |
| `validate_decisions.py` | ✅ NO ISSUES | |
| `validate_localisation.py` | ✅ NO ISSUES | |
| `validate_gfx_references.py` | 120 warnings | All pre-existing (`GFX_ANG_jonas_savimbi` etc.); zero OEM-specific findings |
| `validate_corporate_history_contract.py` | ✅ NO ISSUES | All dispatch, tier-1, clamp, reconstruction, completion-marker, cross-chain checks pass |
| `validate_set_variables.py` | ✅ NO ISSUES | |
| `validate_scripted_localisation.py` | ✅ NO ISSUES | |
| `validate_modifiers.py` | ✅ NO ISSUES | |
| `git diff --check HEAD` | ✅ clean | No conflict markers |

## CI history notes

| SHA | Event |
| --- | --- |
| `a2f9db3fca` | GitHub Pages deployment failed (unrelated to OEM content) |
| `93737f6319` | Validator Cache cancelled (superseded by next push) |
| `61bee3a1ac` | All required checks passed |
| `556b403bca` | All required checks passed |

## Findings

- Zero blocking CI failures at current main.
- Event/GFX warning counts are pre-existing baselines, not regressions introduced by OEM work.
- The GPU chain fix in #106 eliminated 12 `Unknown trigger-type: stability` errors from `error.log`
  (previously present at `61bee3a1ac`, confirmed by Claude's second-pass log inspection).
