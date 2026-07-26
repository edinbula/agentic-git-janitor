"""Repository inspection domain models."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ChangedFile(BaseModel):
    """A file changed in the repository working tree."""

    status: str
    path: str


class RepositorySummary(BaseModel):
    """Structured result from safe repository inspection."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    repository_name: str
    repository_path: Path
    primary_language: str | None = None
    current_branch: str | None = None

    tracked_file_count: int = Field(default=0, ge=0)
    source_files: list[str] = Field(default_factory=list)
    test_files: list[str] = Field(default_factory=list)
    changed_files: list[ChangedFile] = Field(default_factory=list)
    dependency_files: list[str] = Field(default_factory=list)
    detected_languages: dict[str, int] = Field(default_factory=dict)
