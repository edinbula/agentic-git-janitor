"""Tests for command safety policy."""

from app.safety.command_policy import CommandPolicy


def test_allowlisted_command_is_accepted() -> None:
    assert CommandPolicy().is_allowed("pytest")


def test_unknown_command_is_rejected() -> None:
    assert not CommandPolicy().is_allowed("powershell")


def test_windows_executable_suffix_is_normalized() -> None:
    assert CommandPolicy().is_allowed("pytest.exe")


def test_command_arguments_must_match_approved_shape() -> None:
    policy = CommandPolicy()

    assert policy.validate(["ruff", "check", "."]) is None
    assert policy.validate(["pytest", "-c", "outside.ini"]) is not None


def test_executable_paths_are_rejected() -> None:
    policy = CommandPolicy()

    assert policy.validate(["../pytest"]) is not None
    assert policy.validate([r"C:\tools\pytest.exe"]) is not None
