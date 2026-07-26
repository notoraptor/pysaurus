from pysaurus.core.core_exceptions import ApplicationError


class PysaurusError(ApplicationError):
    pass


class UnknownLanguage(PysaurusError):
    pass


class InvalidFileName(PysaurusError):
    pass


class InvalidDatabaseName(InvalidFileName):
    pass


class PropertyAlreadyExists(PysaurusError):
    pass


class PropertyAlreadyUnique(PysaurusError):
    pass


class PropertyAlreadyMultiple(PysaurusError):
    pass


class PropertyToUniqueError(PysaurusError):
    pass


class BooleanPropertyCannotBeMultiple(PysaurusError):
    """A bool property is always unique.

    Its domain is exactly {False, True}, so holding several values at once
    could only ever mean "the whole domain", which carries no information.
    """


class BooleanPropertyCannotBeEnumerated(PysaurusError):
    """A bool property carries no stored enumeration.

    Its domain is implied by the type itself (see PropType.possible_values),
    so it is never spelled out in property_enumeration -- that table holds
    only its default value.
    """


class PropertyNotFound(PysaurusError):
    pass


class PathAlreadyExists(PysaurusError):
    pass


class DatabaseAlreadyExists(PysaurusError):
    pass


class DatabasePathUnavailable(PysaurusError):
    pass


class InvalidDatabaseJSON(PysaurusError):
    pass


class InvalidMiniaturesJSON(PysaurusError):
    pass


class VideoToJsonError(PysaurusError):
    pass


class VideoThumbnailsToJsonError(PysaurusError):
    pass


class MissingPropertyName(PysaurusError):
    pass


class InvalidPropertyDefinition(PysaurusError):
    pass


class InvalidMultiplePropertyValue(PysaurusError):
    pass


class InvalidUniquePropertyValue(PysaurusError):
    pass


class UniquePropertyMergeConflict(PysaurusError):
    """A moved-video merge would put two different values on a unique property.

    Merging carries the source entry's property values onto the destination; for
    a multiple=False property this cannot union two divergent values without
    corrupting it, so the move is refused. Args: a list of
    (from_id, to_id, property_name, dst_values, src_values) tuples.
    """

    pass


class InvalidPropertyValue(PysaurusError):
    pass


class NoVideos(PysaurusError):
    pass


class ForbiddenVideoFolder(PysaurusError):
    pass


class ForbiddenSourceFolder(PysaurusError):
    pass
