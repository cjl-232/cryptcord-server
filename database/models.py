from datetime import datetime
from secrets import token_hex

from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime, String, Text

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    public_key: Mapped[str] = mapped_column(
        String(44),
        nullable=False,
        unique=True,
    )
    sent_messages: Mapped[list['Message']] = relationship(
        back_populates='sender',
        foreign_keys='Message.sender_id',
        lazy='selectin',
    )
    received_messages: Mapped[list['Message']] = relationship(
        back_populates='recipient',
        foreign_keys='Message.recipient_id',
        lazy='selectin',
    )
    sent_exchange_keys: Mapped[list['ExchangeKey']] = relationship(
        back_populates='sender',
        foreign_keys='ExchangeKey.sender_id',
        lazy='selectin',
    )
    received_exchange_keys: Mapped[list['ExchangeKey']] = relationship(
        back_populates='recipient',
        foreign_keys='ExchangeKey.recipient_id',
        lazy='selectin',
    )

class _TransmittedData(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    signature: Mapped[str] = mapped_column(
        String(88),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
    )
    nonce: Mapped[str] = mapped_column(
        default=lambda: token_hex(16),
        nullable=False,
    )

class Message(_TransmittedData):
    __tablename__ = 'messages'
    __table_args__ = (
        Index('idx_message_retrieval', 'recipient_id', 'timestamp'),
        CheckConstraint('recipient_id != sender_id'),
    )
    encrypted_text: Mapped[str] = mapped_column(
        Text(),
        nullable=False,
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
    )
    sender: Mapped[User] = relationship(
        back_populates='sent_messages',
        foreign_keys=[sender_id],
        lazy='selectin',
    )
    recipient: Mapped[User] = relationship(
        back_populates='received_messages',
        foreign_keys=[recipient_id],
        lazy='selectin',
    )
    @property
    def sender_key(self):
        return self.sender.public_key

class ExchangeKey(_TransmittedData):
    __tablename__ = 'exchange_keys'
    __table_args__ = (
        Index('idx_exchange_key_retrieval', 'recipient_id', 'timestamp'),
        CheckConstraint('recipient_id != sender_id'),
    )
    key: Mapped[str] = mapped_column(
        String(44),
        nullable=False,
    )
    response_to: Mapped[str | None] = mapped_column(
        String(44),
        nullable=True,
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
    )
    sender: Mapped[User] = relationship(
        back_populates='sent_exchange_keys',
        foreign_keys=[sender_id],
        lazy='selectin',
    )
    recipient: Mapped[User] = relationship(
        back_populates='received_exchange_keys',
        foreign_keys=[recipient_id],
        lazy='selectin',
    )
    @property
    def sender_key(self):
        return self.sender.public_key
