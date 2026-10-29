# Create Team router
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Team, User
from schemas import TeamCreate, TeamUpdate
from dependencies.roles import require_role

from datetime import datetime

router = APIRouter(
    prefix="/teams",
    tags=["Teams"]
)

# ============================================================
# 1. CREATE TEAM
# POST /teams/
# SUPER_ADMIN only
# ============================================================

@router.post("/")
def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(
        require_role("SUPER_ADMIN")
    ),
    db: Session = Depends(get_db)
):
    existing_team = db.query(Team).filter(
        Team.team_name == team_data.team_name
    ).first()

    if existing_team:
        raise HTTPException(
            status_code=400,
            detail="Team already exists"
        )

    new_team = Team(
        team_name=team_data.team_name,
        academic_year=team_data.academic_year,
        description=team_data.description,
        is_activate=True,
        created_at=datetime.now()
    )

    db.add(new_team)
    db.commit()
    db.refresh(new_team)

    return {
        "message": "Team created successfully",
        "team_id": new_team.id,
        "team_name": new_team.team_name,
        "academic_year": new_team.academic_year,
        "description": new_team.description,
        "is_activate": new_team.is_activate
    }


# ============================================================
# 2. GET ALL TEAMS
# GET /teams/
# SUPER_ADMIN + TEAM_ADMIN
# ============================================================

@router.get("/")
def get_all_teams(
    current_user: User = Depends(
        require_role("SUPER_ADMIN", "TEAM_ADMIN")
    ),
    db: Session = Depends(get_db)
):
    teams = db.query(Team).all()

    result = []

    for team in teams:
        result.append({
            "id": team.id,
            "team_name": team.team_name,
            "academic_year": team.academic_year,
            "description": team.description,
            "is_activate": team.is_activate
        })

    return {
        "total_teams": len(result),
        "teams": result
    }


# ============================================================
# 3. GET ONE TEAM
# GET /teams/{team_id}
# SUPER_ADMIN only
# ============================================================

@router.get("/{team_id}")
def get_team_by_id(
    team_id: int,
    current_user: User = Depends(
        require_role("SUPER_ADMIN")
    ),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(
        Team.id == team_id
    ).first()

    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found"
        )

    return {
        "id": team.id,
        "team_name": team.team_name,
        "academic_year": team.academic_year,
        "description": team.description,
        "is_activate": team.is_activate
    }


# ============================================================
# 4. UPDATE TEAM
# PUT /teams/{team_id}
# SUPER_ADMIN only
# ============================================================

@router.put("/{team_id}")
def update_team(
    team_id: int,
    team_data: TeamUpdate,
    current_user: User = Depends(
        require_role("SUPER_ADMIN")
    ),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(
        Team.id == team_id
    ).first()

    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found"
        )

    # Update only the values provided
    if team_data.team_name is not None:
        team.team_name = team_data.team_name

    if team_data.academic_year is not None:
        team.academic_year = team_data.academic_year

    if team_data.description is not None:
        team.description = team_data.description

    
    if team_data.is_activate is not None:
        team.is_activate = team_data.is_activate

    # Update team members and team admin when team status changes
    db.query(User).filter(
        User.team_id == team.id,
        User.role.in_(["MEMBER", "TEAM_ADMIN"])
    ).update(
        {User.is_activate: team_data.is_activate},
        synchronize_session=False
    )

    # If a team is deactivated, deactivate all users assigned to it.
    if team_data.is_activate is False:
        db.query(User).filter(
            User.team_id == team.id
        ).update(
            {User.is_activate: False},
            synchronize_session=False
        )

    db.commit()
    db.refresh(team)


    return {
        "message": "Team updated successfully",
        "team_id": team.id,
        "team_name": team.team_name,
        "academic_year": team.academic_year,
        "description": team.description,
        "is_activate": team.is_activate
    }