class PropertyValueModifier:
    __slots__ = ()

    @classmethod
    def lowercase(cls, value: str) -> str:
        return value.strip().lower()

    @classmethod
    def uppercase(cls, value: str) -> str:
        return value.strip().upper()
