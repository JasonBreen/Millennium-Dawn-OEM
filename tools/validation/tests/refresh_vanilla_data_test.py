"""Regression tests for vanilla-derived refresh target selection."""

from refresh_vanilla_data import _parse_targets


def test_default_refresh_excludes_reference_docs():
    assert _parse_targets([]) == ["defines", "gui", "paths", "sprites"]


def test_docs_refresh_requires_explicit_selection():
    assert _parse_targets(["--only", "docs"]) == ["docs"]
