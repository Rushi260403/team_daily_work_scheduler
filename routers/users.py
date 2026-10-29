
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User, Team, TeamAdmin, DailyWork
from schemas import UserCreate, UserLogin, UserUpdate, UserTeamAssign
from services.password_service import hash_password, verify_password
from services.auth_service import create_access_token
from dependencies.auth import get_current_user
from dependencies.roles import require_role

from datetime import datetime

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/register")
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    # Check whether email already exists
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create new user
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        team_id=user_data.team_id,
        created_at=datetime.now()
    )

    # Save user
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role,
        "team_id": new_user.team_id
    }


@router.post("/login")
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not user.is_activate:  # type: ignore
        raise HTTPException(
            status_code=403,
            detail="User account is inactivate"
        )

    password_is_correct = verify_password(
        user_data.password,
        user.password_hash  # type: ignore
    )

    if not password_is_correct:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        user_id=user.id,  # type: ignore
        email=user.email,  # type: ignore
        role=user.role  # type: ignore
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "team_id": user.team_id
        }
    }


@router.get("/me")
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "team_id": current_user.team_id
    }


# Get all users - SUPER_ADMIN only
@router.get("/")
def get_all_users(
    current_user: User = Depends(
        require_role("SUPER_ADMIN")
    ),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()

    result = []

    for user in users:
        result.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "team_id": user.team_id,
            "is_activate": user.is_activate,
            "created_at": user.created_at
        })

    return {
        "total_users": len(result),
        "users": result
    }


# Get team members, including inactive accounts
@router.get("/team-members")
def get_team_admin_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # SUPER_ADMIN can see members from all teams
    if current_user.role == "SUPER_ADMIN":

        members = db.query(User).filter(
            User.role == "MEMBER"
        ).all()

    # TEAM_ADMIN can see members from assigned teams only
    elif current_user.role == "TEAM_ADMIN":

        assignments = db.query(TeamAdmin).filter(
            TeamAdmin.user_id == current_user.id
        ).all()

        if not assignments:
            return {
                "message": "No teams assigned to this TEAM_ADMIN",
                "total_members": 0,
                "members": []
            }

        team_ids = [
            assignment.team_id
            for assignment in assignments
        ]

        members = db.query(User).filter(
            User.team_id.in_(team_ids),
            User.role == "MEMBER"
        ).all()

    else:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this resource"
        )

    result = []

    for member in members:
        team = db.query(Team).filter(
            Team.id == member.team_id
        ).first()

        result.append({
            "user_id": member.id,
            "name": member.name,
            "email": member.email,
            "role": member.role,
            "team_id": member.team_id,
            "team_name": team.team_name if team else None,
            "is_activate": member.is_activate,
            "created_at": member.created_at
        })

    return {
        "total_members": len(result),
        "members": result
    }


@router.get("/team-summary")
def get_team_admin_team_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # SUPER_ADMIN can see all teams
    if current_user.role == "SUPER_ADMIN":

        teams = db.query(Team).all()

    # TEAM_ADMIN can see assigned teams only
    elif current_user.role == "TEAM_ADMIN":

        assignments = db.query(TeamAdmin).filter(
            TeamAdmin.user_id == current_user.id
        ).all()

        if not assignments:
            return {
                "message": "No teams assigned to this TEAM_ADMIN",
                "total_teams": 0,
                "teams": []
            }

        team_ids = [
            assignment.team_id
            for assignment in assignments
        ]

        teams = db.query(Team).filter(
            Team.id.in_(team_ids)
        ).all()

    else:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this resource"
        )

    result = []

    for team in teams:
        # Get active members for the team summary
        members = db.query(User).filter(
            User.team_id == team.id,
            User.role == "MEMBER",
            User.is_activate == True
        ).all()

        member_ids = [
            member.id
            for member in members
        ]

        daily_work = []

        if member_ids:
            daily_work = db.query(DailyWork).filter(
                DailyWork.user_id.in_(member_ids)
            ).all()

        total_work_records = len(daily_work)

        completed_days = sum(
            1
            for work in daily_work
            if work.office_out_time is not None
        )

        pending_days = sum(
            1
            for work in daily_work
            if work.office_out_time is None
        )

        result.append({
            "team_id": team.id,
            "team_name": team.team_name,
            "academic_year": team.academic_year,
            "total_members": len(members),
            "total_work_records": total_work_records,
            "completed_days": completed_days,
            "pending_days": pending_days
        })

    return {
        "total_teams": len(result),
        "teams": result
    }


# Get one user - SUPER_ADMIN only
@router.get("/{user_id}")
def get_user(
    user_id: int,
    current_user: User = Depends(
        require_role("SUPER_ADMIN")
    ),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "team_id": user.team_id,
        "is_activate": user.is_activate,
        "created_at": user.created_at
    }


# Update a user - SUPER_ADMIN only
@router.put("/{user_id}")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(
        require_role("SUPER_ADMIN")
    ),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user_data.email is not None:
        existing_user = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        user.email = user_data.email  # type: ignore

    if user_data.name is not None:
        user.name = user_data.name  # type: ignore

    if user_data.role is not None:
        allowed_roles = [
            "MEMBER",
            "TEAM_ADMIN",
            "SUPER_ADMIN"
        ]

        if user_data.role not in allowed_roles:
            raise HTTPException(
                status_code=400,
                detail="Invalid role"
            )

        user.role = user_data.role  # type: ignore

    if user_data.team_id is not None:
        team = db.query(Team).filter(
            Team.id == user_data.team_id
        ).first()

        if not team:
            raise HTTPException(
                status_code=404,
                detail="Team not found"
            )

        user.team_id = user_data.team_id  # type: ignore

    if user_data.is_activate is not None:
        user.is_activate = user_data.is_activate  # type: ignore

    db.commit()
    db.refresh(user)

    return {
        "message": "User updated successfully",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "team_id": user.team_id,
        "is_activate": user.is_activate
    }


# Activate / deactivate user
@router.patch("/{user_id}/activate")
def activate_deactivate_user(
    user_id: int,
    is_activate: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # SUPER_ADMIN can manage MEMBER and TEAM_ADMIN accounts
    if current_user.role == "SUPER_ADMIN":

        if user.role not in ["MEMBER", "TEAM_ADMIN"]:
            raise HTTPException(
                status_code=403,
                detail="Super Admin can only change Member or Team Admin status"
            )

    # TEAM_ADMIN can manage members in assigned teams only
    elif current_user.role == "TEAM_ADMIN":

        if user.role != "MEMBER":
            raise HTTPException(
                status_code=403,
                detail="Team Admin can only activate or deactivate team members"
            )

        assignments = db.query(TeamAdmin).filter(
            TeamAdmin.user_id == current_user.id
        ).all()

        assigned_team_ids = [
            assignment.team_id
            for assignment in assignments
        ]

        if user.team_id not in assigned_team_ids:
            raise HTTPException(
                status_code=403,
                detail="You can only manage members in your assigned teams"
            )

    else:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to change user status"
        )

    user.is_activate = is_activate  # type: ignore

    db.commit()
    db.refresh(user)

    return {
        "message": "User status updated successfully",
        "user_id": user.id,
        "is_activate": user.is_activate
    }


# Assign Team API - SUPER_ADMIN only
@router.put("/{user_id}/team")
def assign_team_to_user(
    user_id: int,
    team_data: UserTeamAssign,
    current_user: User = Depends(
        require_role("SUPER_ADMIN")
    ),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    team = db.query(Team).filter(
        Team.id == team_data.team_id
    ).first()

    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found"
        )

    if not team.is_activate:  # type: ignore
        raise HTTPException(
            status_code=400,
            detail="Cannot assign user to an inactive team"
        )

    user.team_id = team.id

    db.commit()
    db.refresh(user)

    return {
        "message": "Team assigned to user successfully",
        "user_id": user.id,
        "user_name": user.name,
        "team_id": team.id,
        "team_name": team.team_name
    }
