from sqlalchemy import (Column, Integer, String, Boolean, Date, Time, DateTime, Text, ForeignKey)
from sqlalchemy.orm import relationship

from database import Base

# ==========================================
# TEAM MODEL
# ==========================================

class Team(Base):

    __tablename__ = "teams"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    team_name = Column(
        String(100),
        nullable=False
    )

    academic_year = Column(
        String(20),
        nullable=True
    )

    description = Column(
        String(500),
        nullable=True
    )

    is_activate = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at = Column(
        DateTime,
        nullable=True
    )


# ==========================================
# USER MODEL
# ==========================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(20),
        nullable=False,
        default="MEMBER"
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=True
    )

    is_activate = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at = Column(
        DateTime,
        nullable=True
    )


# ==========================================
# TEAM ADMIN MODEL
# ==========================================

class TeamAdmin(Base):

    __tablename__ = "team_admins"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False
    )

    created_at = Column(
        DateTime,
        nullable=True
    )


# ==========================================
# DAILY WORK MODEL
# ==========================================

class DailyWork(Base):
    __tablename__ = "daily_work"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    work_date = Column(
        Date,
        nullable=False
    )

    office_in_time = Column(
        Time,
        nullable=True
    )

    working_points = Column(
        Text,
        nullable=True
    )

    office_out_time = Column(
        Time,
        nullable=True
    )

    points_completed = Column(
        Text,
        nullable=True
    )

    pending_points = Column(
        Text,
        nullable=True
    )

    morning_message = Column(
        Text,
        nullable=True
    )

    evening_message = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        nullable=True
    )

    updated_at = Column(
        DateTime,
        nullable=True
    )
# ==========================================
# USER SETTINGS MODEL
# ==========================================

class UserSettings(Base):

    __tablename__ = "user_settings"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    morning_reminder_time = Column(
        Time,
        nullable=True
    )

    evening_reminder_time = Column(
        Time,
        nullable=True
    )

    notifications_enabled = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at = Column(
        DateTime,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        nullable=True
    )

class HistoricalEditRequest(Base):
    __tablename__ = "historical_edit_requests"

    id = Column(Integer, primary_key=True, index=True)

    daily_work_id = Column(
        Integer,
        ForeignKey("daily_work.id"),
        nullable=False
    )

    requested_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    request_reason = Column(String(1000), nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="PENDING"
    )

    reviewed_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    review_comment = Column(String(1000), nullable=True)

    requested_at = Column(DateTime, nullable=False)

    reviewed_at = Column(DateTime, nullable=True)

    used_at = Column(DateTime, nullable=True)


class HistoricalWorkEditAudit(Base):
    __tablename__ = "historical_work_edit_audit"

    id = Column(Integer, primary_key=True, index=True)

    daily_work_id = Column(
        Integer,
        ForeignKey("daily_work.id"),
        nullable=False
    )

    edit_request_id = Column(
        Integer,
        ForeignKey("historical_edit_requests.id"),
        nullable=False
    )

    edited_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    old_values = Column(Text, nullable=False)

    new_values = Column(Text, nullable=False)

    edited_at = Column(
        DateTime,
        nullable=False
    )
