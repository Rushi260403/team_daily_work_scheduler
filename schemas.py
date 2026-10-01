from pydantic import BaseModel, EmailStr
from datetime import date, time

class UserCreate(BaseModel):
    name:str
    email:EmailStr
    password:str
    role:str = "MEMBER"
    team_id:int | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TeamCreate(BaseModel):
    team_name: str
    academic_year: str | None = None
    description: str | None = None

class TeamUpdate(BaseModel):
    team_name: str | None = None
    academic_year: str | None = None
    description: str | None = None
    is_activate: bool | None = None

class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    role: str | None = None
    team_id: int | None = None
    is_activate: bool | None = None

class UserTeamAssign(BaseModel):
    team_id: int

# Phase 9 — Daily Work Management
# 9.1 Create Daily Work Schemas
class MorningWorkCreate(BaseModel):
    work_date: date
    office_in_time: time
    working_points: str


class EveningWorkUpdate(BaseModel):
    office_out_time: time
    points_completed: str
    pending_points: str


class DailyWorkResponse(BaseModel):
    id: int
    user_id: int
    work_date: date
    office_in_time: time | None = None
    working_points: str | None = None
    office_out_time: time | None = None
    points_completed: str | None = None
    pending_points: str | None = None
    morning_message: str | None = None
    evening_message: str | None = None