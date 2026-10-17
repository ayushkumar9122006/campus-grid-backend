from contextlib import AbstractContextManager
from typing import Callable, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from campus_grid.model.user import User
from campus_grid.repository.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]):
        super().__init__(session_factory, User)

    def get_by_email(self, email: str) -> Optional[User]:
        with self.session_factory() as session:
            stmt = select(User).where(User.email == email.strip().lower())
            return session.scalar(stmt)
