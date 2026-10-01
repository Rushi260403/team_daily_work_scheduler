from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import TeamAdmin, User, Team
from dependencies.roles import require_role


router = APIRouter(
    prefix="/team-admins",
    tags=["Team Admins"]
)


@router.post("/")
def assign_team_admin(
    user_id: int,
    team_id: int,
    current_user: User = Depends(
        require_role("SUPER_ADMIN")
    ),
    db: Session = Depends(get_db)
):

    # Check user
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # User must be TEAM_ADMIN
    if user.role != "TEAM_ADMIN": # type: ignore
        raise HTTPException(
            status_code=400,
            detail="User must have TEAM_ADMIN role"
        )

    # User must be active
    if not user.is_activate: # type: ignore
        raise HTTPException(
            status_code=400,
            detail="User account is inactive"
        )

    # Check team
    team = db.query(Team).filter(
        Team.id == team_id
    ).first()

    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found"
        )

    # Team must be active
    if not team.is_activate: # type: ignore
        raise HTTPException(
            status_code=400,
            detail="Cannot assign admin to an inactive team"
        )

    # Check duplicate assignment
    existing_assignment = db.query(TeamAdmin).filter(
        TeamAdmin.user_id == user_id,
        TeamAdmin.team_id == team_id
    ).first()

    if existing_assignment:
        raise HTTPException(
            status_code=400,
            detail="This TEAM_ADMIN is already assigned to this team"
        )

    # Create assignment
    new_assignment = TeamAdmin(
        user_id=user_id,
        team_id=team_id,
        created_at=datetime.now()
    )

    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)

    return {
        "message": "TEAM_ADMIN assigned to team successfully",
        "assignment_id": new_assignment.id,
        "user_id": user.id,
        "user_name": user.name,
        "team_id": team.id,
        "team_name": team.team_name
    }

# GET API of team_admin_assignments
@router.get("/")
def get_team_admin_assignments(
    current_user: User = Depends(
        require_role("SUPER_ADMIN")
    ),
    db: Session = Depends(get_db)
):

    assignments = db.query(TeamAdmin).all()

    result = []

    for assignment in assignments:

        user = db.query(User).filter(
            User.id == assignment.user_id
        ).first()

        team = db.query(Team).filter(
            Team.id == assignment.team_id
        ).first()

        result.append({
            "assignment_id": assignment.id,
            "user_id": assignment.user_id,
            "user_name": user.name if user else None,
            "user_email": user.email if user else None,
            "team_id": assignment.team_id,
            "team_name": team.team_name if team else None,
            "created_at": assignment.created_at
        })

    return {
        "total_assignments": len(result),
        "assignments": result
    }

# Add DELETE API for TeamAdmin
@router.delete("/{assignment_id}")
def remove_team_admin_assignment(
    assignment_id: int,
    current_user: User = Depends(
        require_role("SUPER_ADMIN")
    ),
    db: Session = Depends(get_db)
):

    assignment = db.query(TeamAdmin).filter(
        TeamAdmin.id == assignment_id
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Team admin assignment not found"
        )

    db.delete(assignment)
    db.commit()

    return {
        "message": "TEAM_ADMIN removed from team successfully",
        "assignment_id": assignment_id
    }