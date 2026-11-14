from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Text, text, Identity
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import ForeignKey, Index

class Base(DeclarativeBase):
    pass


class Link(Base):
    __tablename__ = "links"
    owner_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable= True)

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    original_url: Mapped[str] = mapped_column(Text)
    clicks: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

Index(
    "ix_links_owner_created_code",
    Link.owner_id,
    Link.created_at.desc(),
    Link.code.desc(),
)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )
    username: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
