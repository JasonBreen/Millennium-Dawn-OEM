import codecs
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validate_localization_encoding import LocalizationValidator


def test_missing_bom_is_rejected(tmp_path):
    path = tmp_path / "missing_l_english.yml"
    path.write_bytes(b'l_english:\n KEY: "Value"\n')
    validator = LocalizationValidator()

    assert not validator.validate_file(path)
    assert any("Missing UTF-8 BOM" in error for error in validator.errors)


def test_invalid_utf8_after_bom_is_rejected(tmp_path):
    path = tmp_path / "invalid_l_english.yml"
    path.write_bytes(codecs.BOM_UTF8 + b'l_english:\n KEY: "\xff"\n')
    validator = LocalizationValidator()

    assert not validator.validate_file(path)
    assert any("Invalid UTF-8 encoding" in error for error in validator.errors)


def test_valid_utf8_bom_file_is_accepted(tmp_path):
    path = tmp_path / "valid_l_english.yml"
    path.write_bytes(codecs.BOM_UTF8 + 'l_english:\n KEY: "Café"\n'.encode())
    validator = LocalizationValidator()

    assert validator.validate_file(path)
    assert validator.errors == []
