from contextlib import AbstractContextManager, contextmanager
from typing import Any, Callable, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

from campus_grid.model.base_model import Base


class Database:
    def __init__(self, db_url: str) -> None:
        engine_args = {}
        if db_url.startswith("sqlite"):
            engine_args["connect_args"] = {"check_same_thread": False}
            if ":memory:" in db_url:
                engine_args["poolclass"] = StaticPool

        self._engine = create_engine(db_url, **engine_args)
        self._session_factory = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine,
            ),
        )

    def create_database(self) -> None:
        Base.metadata.create_all(self._engine)

    def drop_database(self) -> None:
        Base.metadata.drop_all(self._engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @property
    def session_factory(self) -> Callable[..., AbstractContextManager[Session]]:
        return self.session
