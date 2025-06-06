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
    received_messages: Mapped[list['EncryptedMessage']] = relationship(
        back_populates='recipient',
        foreign_keys='EncryptedMessage.recipient_id',
        lazy='selectin',
    )
    sent_messages: Mapped[list['EncryptedMessage']] = relationship(
        back_populates='sender',
        foreign_keys='EncryptedMessage.sender_id',
        lazy='selectin',
    )
    received_key_exchanges: Mapped[list['KeyExchange']] = relationship(
        back_populates='recipient',
        foreign_keys='KeyExchange.recipient_id',
        lazy='selectin',
    )
    sent_key_exchanges: Mapped[list['KeyExchange']] = relationship(
        back_populates='sender',
        foreign_keys='KeyExchange.sender_id',
        lazy='selectin',
    )

class EncryptedMessage(Base):
    __tablename__ = 'encrypted_messages'
    __table_args__ = (
        Index('idx_message_retrieval', 'recipient_id', 'timestamp'),
        CheckConstraint('recipient_id != sender_id'),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    encrypted_text: Mapped[str] = mapped_column(
        Text(),
    )
    signature: Mapped[str] = mapped_column(
        String(88),
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
    )
    nonce: Mapped[str] = mapped_column(
        default=lambda: token_hex(16),
    )
    recipient: Mapped[User] = relationship(
        back_populates='received_messages',
        foreign_keys=[recipient_id],
        lazy='selectin',
    )
    sender: Mapped[User] = relationship(
        back_populates='sent_messages',
        foreign_keys=[sender_id],
        lazy='selectin',
    )

class KeyExchange(Base):
    __tablename__ = 'key_exchanges'
    __table_args__ = (
        Index('idx_key_exchange_retrieval', 'recipient_id', 'timestamp'),
        CheckConstraint('recipient_id != sender_id'),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    x25519_public_key: Mapped[str] = mapped_column(
        String(44),
    )
    signature: Mapped[str] = mapped_column(
        String(88),
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
    )
    recipient: Mapped[User] = relationship(
        back_populates='received_key_exchanges',
        foreign_keys=[recipient_id],
        lazy='selectin',
    )
    sender: Mapped[User] = relationship(
        back_populates='sent_key_exchanges',
        foreign_keys=[sender_id],
        lazy='selectin',
    )
