class PropertyValueModifier:
    __slots__ = ()

    @classmethod
    def lowercase(cls, value: str) -> str:
        """Convert to lowercase."""
        return value.strip().lower()

    @classmethod
    def uppercase(cls, value: str) -> str:
        """Convert to uppercase."""
        return value.strip().upper()

    @classmethod
    def titlecase(cls, value: str) -> str:
        """Convert to title case (capitalize each word)."""
        return value.strip().title()

    @classmethod
    def capitalize(cls, value: str) -> str:
        """Capitalize first letter only."""
        return value.strip().capitalize()

    @classmethod
    def strip(cls, value: str) -> str:
        """Remove leading/trailing whitespace."""
        return value.strip()

    @classmethod
    def get_modifiers(cls) -> list[str]:
        """Return list of available modifier names."""
        return [
            name
            for name in dir(cls)
            if not name.startswith("_")
            and name != "get_modifiers"
            and callable(getattr(cls, name))
        ]
