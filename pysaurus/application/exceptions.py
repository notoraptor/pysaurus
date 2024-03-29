from pysaurus.core.core_exceptions import ApplicationError


class PysaurusError(ApplicationError):
    pass


class MissingLanguageFile(PysaurusError):
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


class InvalidPropertyValue(PysaurusError):
    pass


class NoVideos(PysaurusError):
    pass


class ForbiddenVideoFolder(PysaurusError):
    pass


class CysaurusUnavailable(PysaurusError):
    pass
