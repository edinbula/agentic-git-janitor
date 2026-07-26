"""Tests for command safety policy."""

from app.safety.command_policy import CommandPolicy


def test_allowlisted_command_is_accepted() -> None:
    assert CommandPolicy().is_allowed("pytest")


def test_unknown_command_is_rejected() -> None:
    assert not CommandPolicy().is_allowed("powershell")
