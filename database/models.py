from datetime import datetime

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

class EncryptedMessage(Base):
    __tablename__ = 'encrypted_messages'
    __table_args__ = (
        Index('idx_msgs_retrieval', 'recipient_id', 'timestamp'),
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
