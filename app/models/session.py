from sqlalchemy import (
    String, Integer, DateTime, ForeignKey,
    Enum, JSON, Boolean, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, composite
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List, Any
from app.core.database import Base
from app.models.value_objects import VotingDuration
import enum


class SessionStatus(str, enum.Enum):
    WAITING = "waiting"
    EDITING = "editing"
    READY = "ready"
    VOTING = "voting"
    RESULTS = "results"
    CLOSED = "closed"


class SessionMode(str, enum.Enum):
    RANDOM = "random"
    RANKING = "ranking"


class ParticipantStatus(str, enum.Enum):
    INVITED = "invited"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    LEFT = "left"
    KICKED = "kicked"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    current_list_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("session_lists.id", ondelete="SET NULL"), nullable=True)
    mode: Mapped[SessionMode] = mapped_column(Enum(SessionMode), nullable=False, default=SessionMode.RANKING)
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.WAITING, nullable=False)
    list_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    voting_duration_seconds: Mapped[int] = mapped_column("voting_duration", Integer, default=120)
    voting_duration: Mapped[VotingDuration] = composite(VotingDuration, voting_duration_seconds)
    countdown_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    voting_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    results_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    owner = relationship("User", foreign_keys=[owner_id], backref="owned_sessions")
    closer = relationship("User", foreign_keys=[closed_by])
    session_lists = relationship("SessionList", back_populates="session", foreign_keys="SessionList.session_id", cascade="all, delete-orphan")
    current_list = relationship("SessionList", foreign_keys=[current_list_id], post_update=True)
    participants = relationship("SessionParticipant", back_populates="session", cascade="all, delete-orphan")
    results = relationship("SessionResult", back_populates="session", cascade="all, delete-orphan")


class SessionList(Base):
    __tablename__ = "session_lists"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    session = relationship("Session", back_populates="session_lists", foreign_keys=[session_id])
    items = relationship("SessionListItem", back_populates="session_list", cascade="all, delete-orphan", order_by="SessionListItem.order_index")


class SessionListItem(Base):
    __tablename__ = "session_list_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_list_id: Mapped[int] = mapped_column(Integer, ForeignKey("session_lists.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    edited_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    session_list = relationship("SessionList", back_populates="items")
    creator = relationship("User", foreign_keys=[created_by])
    editor = relationship("User", foreign_keys=[edited_by])


class SessionParticipant(Base):
    __tablename__ = "session_participants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[ParticipantStatus] = mapped_column(Enum(ParticipantStatus), default=ParticipantStatus.INVITED, nullable=False)
    is_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    has_voted: Mapped[bool] = mapped_column(Boolean, default=False)
    vote_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    has_spun: Mapped[bool] = mapped_column(Boolean, default=False)
    invited_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    invited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    joined_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ready_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    voted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    session = relationship("Session", back_populates="participants")
    user = relationship("User", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])


class SessionResult(Base):
    __tablename__ = "session_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    session_list_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("session_list_items.id", ondelete="CASCADE"), nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    place: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    session = relationship("Session", back_populates="results")
    list_item = relationship("SessionListItem", foreign_keys=[session_list_item_id])