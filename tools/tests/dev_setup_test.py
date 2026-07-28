import pytest
from unittest.mock import patch
from tools.dev_setup import check_dev_packages

@patch("tools.dev_setup._check_group")
def test_check_dev_packages_true(mock_check_group):
    mock_check_group.return_value = True
    assert check_dev_packages() is True
    mock_check_group.assert_called_once_with("dev", "Dev/test dependencies")

@patch("tools.dev_setup._check_group")
def test_check_dev_packages_false(mock_check_group):
    mock_check_group.return_value = False
    assert check_dev_packages() is False
    mock_check_group.assert_called_once_with("dev", "Dev/test dependencies")
