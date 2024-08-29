import environ
import structlog
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from models import HTTPRequest, SSHRequest

DATABASE_FILE = "/data/app.db"

log = structlog.get_logger(__name__)

env = environ.Env()
ECHO_SQL_QUERIES = env("ECHO_SQL_QUERIES", default=False, cast=bool)
SQL_QUERY_TIMEOUT = env("SQL_QUERY_TIMEOUT", default=30, cast=int)


async def _persist_request(request):
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{DATABASE_FILE}",
        echo=ECHO_SQL_QUERIES,
        connect_args={"timeout": SQL_QUERY_TIMEOUT},
    )

    async with AsyncSession(engine) as session:
        async with session.begin():
            session.add(request)

        await session.commit()

    await engine.dispose()


async def create_http_request_database_entry(
    path, method, remote_id, started, finished
):
    request = HTTPRequest(
        path=path,
        method=method,
        remote_ip=remote_id,
        request_started=started,
        request_finished=finished,
    )

    await _persist_request(request)


async def create_ssh_request_database_entry(
    username, password, remote_ip, started, finished
):
    request = SSHRequest(
        username=username,
        password=password,
        remote_ip=remote_ip,
        request_started=started,
        request_finished=finished,
    )

    await _persist_request(request)
