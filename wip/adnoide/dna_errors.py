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
