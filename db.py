from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from main import log
from models import Base, HTTPRequest

DATABASE_FILE = "/data/app.db"


async def create_database_entry(path, method, remote_id, started, finished):
    request = HTTPRequest(
        path=path,
        method=method,
        remote_ip=remote_id,
        request_started=started,
        request_finished=finished,
    )

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{DATABASE_FILE}", echo=True, connect_args={"timeout": 15}
    )

    async with AsyncSession(engine) as session:
        async with session.begin():
            session.add(request)

        await session.commit()

    await engine.dispose()


async def setup_database():
    log.info(f"Creating database {DATABASE_FILE}")
    engine = create_async_engine(f"sqlite+aiosqlite:///{DATABASE_FILE}", echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
