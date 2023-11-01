import logging
from abc import ABCMeta, abstractmethod

from pysaurus.database.abstract_database import AbstractDatabase

logger = logging.getLogger(__name__)


class AbstractJsonDatabase(AbstractDatabase, metaclass=ABCMeta):
    __slots__ = ()

    def __close__(self):
        """Close database."""
        logger.info(f"Database closed: {self.get_name()}")

    @abstractmethod
    def set_predictor(self, prop_name, theta):
        raise NotImplementedError()

    @abstractmethod
    def get_predictor(self, prop_name):
        raise NotImplementedError()

    @abstractmethod
    def create_prop_type(self, name, prop_type, definition, multiple):
        raise NotImplementedError()

    @abstractmethod
    def remove_prop_type(self, name):
        raise NotImplementedError()

    @abstractmethod
    def rename_prop_type(self, old_name, new_name):
        raise NotImplementedError()

    @abstractmethod
    def convert_prop_multiplicity(self, name, multiple):
        raise NotImplementedError()

    @abstractmethod
    def get_prop_values(self, video_id, name):
        raise NotImplementedError()

    @abstractmethod
    def validate_prop_values(self, name, values):
        raise NotImplementedError()

    @abstractmethod
    def set_video_properties(self, video_id, properties):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def _video_must_be_updated(cls, video):
        raise NotImplementedError()

    @abstractmethod
    def get_video_terms(self, video_id):
        raise NotImplementedError()

    @abstractmethod
    def move_video_entry(self, from_id, to_id):
        raise NotImplementedError()

    @abstractmethod
    def confirm_unique_moves(self):
        raise NotImplementedError()

    @abstractmethod
    def describe_videos(self, video_indices, with_moves):
        raise NotImplementedError()

    @abstractmethod
    def get_common_fields(self, video_indices):
        raise NotImplementedError()

    @abstractmethod
    def select_prop_types(
        self, *, name=None, with_type=None, multiple=None, with_enum=None, default=None
    ):
        pass
