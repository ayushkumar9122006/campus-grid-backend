from typing import Any, Generic, TypeVar
from campus_grid.repository.base_repository import BaseRepository

T = TypeVar("T")


class BaseService(Generic[T]):
    def __init__(self, repository: BaseRepository[T]) -> None:
        self.repository = repository

    def get_by_id(self, id: int) -> T:
        return self.repository.get_by_id_or_raise(id)

    def close_scoped_session(self) -> None:
        pass
