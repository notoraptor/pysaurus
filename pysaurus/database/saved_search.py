from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class SavedSearch:
    """A searchexp expression a database remembers, under an optional name."""

    expression: str
    name: str | None = None

    @property
    def label(self) -> str:
        return self.name or self.expression
