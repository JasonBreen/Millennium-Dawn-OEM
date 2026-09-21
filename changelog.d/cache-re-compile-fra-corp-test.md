# Performance Optimization: Cache regex compilation in FRA corporate systems state model test

Cached regex patterns using `@functools.lru_cache(maxsize=128)` for parameterized regexes and module-level compiled constants for static regexes in `tools/tests/fra_corporate_systems_state_model_test.py`.
