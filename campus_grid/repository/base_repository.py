from contextlib import AbstractContextManager
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from campus_grid.core.exceptions import NotFoundError
from campus_grid.model.base_model import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]], model: Type[T]) -> None:
        self.session_factory = session_factory
        self.model = model

    def create(self, entity: T) -> T:
        with self.session_factory() as session:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity

    def get_by_id(self, id: int) -> Optional[T]:
        with self.session_factory() as session:
            stmt = select(self.model).where(self.model.id == id)
            return session.scalar(stmt)

    def get_by_id_or_raise(self, id: int) -> T:
        item = self.get_by_id(id)
        if not item:
            raise NotFoundError(detail=f"{self.model.__name__} with ID {id} not found")
        return item

    def list(
        self,
        offset: int = 0,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[Any] = None,
    ) -> List[T]:
        with self.session_factory() as session:
            stmt = select(self.model)
            if filters:
                for attr_name, value in filters.items():
                    if hasattr(self.model, attr_name) and value is not None:
                        stmt = stmt.where(getattr(self.model, attr_name) == value)
            if order_by is not None:
                stmt = stmt.order_by(order_by)
            else:
                stmt = stmt.order_by(self.model.id.desc())
            stmt = stmt.offset(offset).limit(limit)
            return list(session.scalars(stmt).all())

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        with self.session_factory() as session:
            stmt = select(func.count()).select_from(self.model)
            if filters:
                for attr_name, value in filters.items():
                    if hasattr(self.model, attr_name) and value is not None:
                        stmt = stmt.where(getattr(self.model, attr_name) == value)
            return session.scalar(stmt) or 0

    def update(self, id: int, updates: Dict[str, Any]) -> Optional[T]:
        with self.session_factory() as session:
            stmt = select(self.model).where(self.model.id == id)
            entity = session.scalar(stmt)
            if not entity:
                return None
            for key, value in updates.items():
                if hasattr(entity, key) and value is not None:
                    setattr(entity, key, value)
            session.commit()
            session.refresh(entity)
            return entity

    def delete(self, id: int) -> bool:
        with self.session_factory() as session:
            stmt = select(self.model).where(self.model.id == id)
            entity = session.scalar(stmt)
            if not entity:
                return False
            session.delete(entity)
            session.commit()
            return True
