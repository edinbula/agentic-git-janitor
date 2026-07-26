"""Command allowlist for future QA execution."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandPolicy:
    """Restrict commands that automated agents may execute."""

    allowed_executables: frozenset[str] = frozenset(
        {
            "python",
            "python3",
            "pytest",
            "ruff",
            "mypy",
            "bandit",
        }
    )

    def is_allowed(self, executable: str) -> bool:
        """Return whether an executable is allowlisted."""
        normalized = executable.strip().lower()
        return normalized in self.allowed_executables
