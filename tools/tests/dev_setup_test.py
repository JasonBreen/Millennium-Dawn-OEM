from unittest.mock import patch

from tools.dev_setup import check_bun, check_dev_packages


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


@patch("tools.dev_setup.get_version")
@patch("tools.dev_setup._resolve_tool")
def test_check_bun_installed(mock_resolve, mock_get_version, capsys):
    mock_resolve.return_value = ["/path/to/bun"]
    mock_get_version.return_value = "1.0.0"

    result = check_bun()

    assert result is True
    mock_resolve.assert_called_once_with("bun")
    mock_get_version.assert_called_once_with(["/path/to/bun", "--version"])

    captured = capsys.readouterr()
    assert "Bun: 1.0.0" in captured.out


@patch("tools.dev_setup.get_version")
@patch("tools.dev_setup._resolve_tool")
def test_check_bun_not_installed(mock_resolve, mock_get_version, capsys):
    mock_resolve.return_value = ["bun"]
    mock_get_version.return_value = None

    result = check_bun()

    assert result is False
    mock_resolve.assert_called_once_with("bun")
    mock_get_version.assert_called_once_with(["bun", "--version"])

    captured = capsys.readouterr()
    assert "Bun: not installed" in captured.out
