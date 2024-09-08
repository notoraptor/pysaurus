class PropertyValueModifier:
    __slots__ = ()

    @classmethod
    def lowercase(self, value: str) -> str:
        return value.strip().lower()

    @classmethod
    def uppercase(self, value: str) -> str:
        return value.strip().upper()
