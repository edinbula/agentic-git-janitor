"""Command allowlist for future QA execution."""

from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath


@dataclass(frozen=True)
class CommandPolicy:
    """Restrict commands that automated agents may execute."""

    allowed_executables: frozenset[str] = frozenset(
        {
            "pytest",
            "ruff",
            "mypy",
            "bandit",
        }
    )

    def is_allowed(self, executable: str) -> bool:
        """Return whether an executable is allowlisted."""
        normalized = executable.strip().lower()
        if normalized.endswith(".exe"):
            normalized = normalized[:-4]
        return normalized in self.allowed_executables

    def validate(self, args: list[str]) -> str | None:
        """Return a rejection reason unless arguments match a safe command shape."""
        if not args:
            return "Empty validation commands are not permitted."
        raw_executable = args[0].strip()
        if (
            PurePosixPath(raw_executable).name != raw_executable
            or PureWindowsPath(raw_executable).name != raw_executable
        ):
            return "Validation executables must be bare allowlisted command names."
        executable = raw_executable.lower()
        if executable.endswith(".exe"):
            executable = executable[:-4]
        if executable not in self.allowed_executables:
            return f"Executable '{raw_executable}' is not allowlisted."

        permitted: dict[str, set[tuple[str, ...]]] = {
            "pytest": {()},
            "ruff": {("check", "."), ("format", "--check", ".")},
            "mypy": {("app",)},
            "bandit": {("-q", "-r", "app")},
        }
        arguments = tuple(args[1:])
        if arguments not in permitted[executable]:
            return (
                f"Arguments for '{raw_executable}' do not match an approved "
                "validation command."
            )
        return None
