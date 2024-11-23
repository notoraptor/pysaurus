class DNAError(Exception):
    pass


class DNATranslationError(DNAError):
    pass


class DNATooShortForTranslationError(DNATranslationError):
    pass


class DNATooLongForTranslationError(DNATranslationError):
    pass


class ProteinError(DNAError):
    pass


class ConstantProteinError(ProteinError):
    pass


class ProteinTypeError(ProteinError):
    pass


class ProteinArgsError(ProteinError):
    def __init__(self, expected: int, given: int):
        super().__init__(f"Protein expected {expected} args, got {given}")
