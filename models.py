from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class HTTPRequest(Base):
    __tablename__ = "http_request"

    id: Mapped[int] = mapped_column(primary_key=True)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    path: Mapped[str]
    method: Mapped[str]

    remote_ip: Mapped[str]
    request_started: Mapped[datetime]
    request_finished: Mapped[datetime]
