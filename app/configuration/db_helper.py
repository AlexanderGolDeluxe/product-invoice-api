from asyncio import current_task

from sqlalchemy.ext.asyncio import (
    async_scoped_session, async_sessionmaker, create_async_engine
)
from sqlalchemy.pool import NullPool

from app.config import DB_URL, DEBUG_MODE


class DatabaseHelper:

    def __init__(self, db_url: str, echo_mode: bool = False):
        self.engine = create_async_engine(
            url=db_url, echo=echo_mode, poolclass=NullPool
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False)

    def get_scoped_session(self):
        session = async_scoped_session(
            session_factory=self.session_factory,
            scopefunc=current_task
        )
        return session

    async def scoped_session_dependency(self):
        session = self.get_scoped_session()
        yield session
        await session.close()


db_helper = DatabaseHelper(db_url=DB_URL, echo_mode=DEBUG_MODE)
