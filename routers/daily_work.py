from datetime import datetime, date
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import DailyWork, User, TeamAdmin, Team, HistoricalEditRequest, HistoricalWorkEditAudit
from schemas import (
    MorningWorkCreate,
    EveningWorkUpdate,
    HistoricalEditRequestCreate,
    HistoricalEditRequestReview,
    HistoricalWorkEdit
)
from dependencies.auth import get_current_user

import json

def get_today_date() -> date:
    """Return today's date using India Standard Time."""
    from datetime import timedelta, timezone

    india_timezone = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(india_timezone).date()

router = APIRouter(
    prefix="/daily-work",
    tags=["Daily Work"]
)

# ============================================================
# 1. SUBMIT MORNING WORK
# ============================================================

@router.post("/morning")
def create_morning_work(
    work_data: MorningWorkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Allow submissions only for today's date
    today = get_today_date()

    if work_data.work_date != today:
        raise HTTPException(
            status_code=400,
            detail=f"Morning Work can only be submitted for today ({today})."
        )

    # Check whether work already exists for this date
    existing_work = db.query(DailyWork).filter(
        DailyWork.user_id == current_user.id,
        DailyWork.work_date == work_data.work_date
    ).first()

    if existing_work:
        raise HTTPException(
            status_code=400,
            detail="Daily work already exists for this date."
        )

    # Create morning message
    morning_message = (
        f"Date: {work_data.work_date}. "
        f"Office In Time: {work_data.office_in_time}. "
        f"Working Points: {work_data.working_points}"
    )

    # Create new daily work record
    new_work = DailyWork(
        user_id=current_user.id,
        work_date=work_data.work_date,
        office_in_time=work_data.office_in_time,
        working_points=work_data.working_points,
        morning_message=morning_message,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(new_work)
    db.commit()
    db.refresh(new_work)

    return {
        "message": "Morning work saved successfully",
        "daily_work_id": new_work.id,
        "user_id": new_work.user_id,
        "work_date": new_work.work_date,
        "office_in_time": new_work.office_in_time,
        "working_points": new_work.working_points,
        "morning_message": new_work.morning_message
    }

# ============================================================
# 2. SUBMIT EVENING WORK
# ============================================================

@router.put("/evening/{work_date}")
def update_evening_work(
    work_date: date,
    work_data: EveningWorkUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Allow submissions only for today's date
    today = get_today_date()

    if work_date != today:
        raise HTTPException(
            status_code=400,
            detail=f"Evening Work can only be submitted for today ({today})."
        )

    # Find the user's daily work record
    existing_work = db.query(DailyWork).filter(
        DailyWork.user_id == current_user.id,
        DailyWork.work_date == work_date
    ).first()

    # Morning Work must exist first
    if not existing_work:
        raise HTTPException(
            status_code=404,
            detail="Morning Work has not been submitted for this date."
        )

    # Reject duplicate Evening Work submissions
    if existing_work.office_out_time is not None:
        raise HTTPException(
            status_code=409,
            detail="Evening Work has already been submitted for this date."
        )

    # Save Evening Work
    existing_work.office_out_time = work_data.office_out_time
    existing_work.points_completed = work_data.points_completed
    existing_work.pending_points = (
        work_data.pending_points.strip()
        if work_data.pending_points
        else ""
    )

    # Create the Evening Work message
    existing_work.evening_message = (
        f"Date: {existing_work.work_date}. "
        f"Office Out Time: {work_data.office_out_time}. "
        f"Points Completed: {work_data.points_completed}. "
        f"Pending Points: {existing_work.pending_points}"
    )

    existing_work.updated_at = datetime.now()

    db.commit()
    db.refresh(existing_work)

    return {
        "message": "Evening Work saved successfully.",
        "daily_work_id": existing_work.id,
        "user_id": existing_work.user_id,
        "work_date": existing_work.work_date,
        "office_in_time": existing_work.office_in_time,
        "office_out_time": existing_work.office_out_time,
        "working_points": existing_work.working_points,
        "points_completed": existing_work.points_completed,
        "pending_points": existing_work.pending_points,
        "evening_message": existing_work.evening_message
    }


# ============================================================
# 3. MEMBER - MY DAILY WORK
# ============================================================

@router.get("/my")
def get_my_daily_work(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    daily_work = db.query(DailyWork).filter(
        DailyWork.user_id == current_user.id
    ).order_by(
        DailyWork.work_date.desc()
    ).all()

    result = []

    for work in daily_work:
        result.append({
            "id": work.id,
            "user_id": work.user_id,
            "work_date": work.work_date,
            "office_in_time": work.office_in_time,
            "working_points": work.working_points,
            "office_out_time": work.office_out_time,
            "points_completed": work.points_completed,
            "pending_points": work.pending_points,
            "morning_message": work.morning_message,
            "evening_message": work.evening_message,
            "created_at": work.created_at,
            "updated_at": work.updated_at
        })

    return {
        "total_records": len(result),
        "daily_work": result
    }


# ============================================================
# 4. MEMBER - MY DAILY WORK BY DATE
# ============================================================

@router.get("/my/{work_date}")
def get_my_daily_work_by_date(
    work_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    daily_work = db.query(DailyWork).filter(
        DailyWork.user_id == current_user.id,
        DailyWork.work_date == work_date
    ).first()

    if not daily_work:
        raise HTTPException(
            status_code=404,
            detail="Daily work not found for this date"
        )

    return {
        "id": daily_work.id,
        "user_id": daily_work.user_id,
        "work_date": daily_work.work_date,
        "office_in_time": daily_work.office_in_time,
        "working_points": daily_work.working_points,
        "office_out_time": daily_work.office_out_time,
        "points_completed": daily_work.points_completed,
        "pending_points": daily_work.pending_points,
        "morning_message": daily_work.morning_message,
        "evening_message": daily_work.evening_message,
        "created_at": daily_work.created_at,
        "updated_at": daily_work.updated_at
    }


# ============================================================
# 5. MEMBER - USER DASHBOARD
# ============================================================


@router.get("/dashboard")
def get_user_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # TEAM_ADMIN: Get work records from assigned teams
    if current_user.role == "TEAM_ADMIN":

        assignments = db.query(TeamAdmin).filter(
            TeamAdmin.user_id == current_user.id
        ).all()

        team_ids = [
            assignment.team_id
            for assignment in assignments
        ]

        if team_ids:
            team_members = db.query(User).filter(
                User.team_id.in_(team_ids),
                User.role == "MEMBER",
                User.is_activate == True
            ).all()

            member_ids = [
                member.id
                for member in team_members
            ]

            if member_ids:
                daily_work = db.query(DailyWork).filter(
                    DailyWork.user_id.in_(member_ids)
                ).order_by(
                    DailyWork.work_date.desc()
                ).all()
            else:
                daily_work = []
        else:
            daily_work = []

    # Other roles: retain the logged-in user's own work
    else:
        daily_work = db.query(DailyWork).filter(
            DailyWork.user_id == current_user.id
        ).order_by(
            DailyWork.work_date.desc()
        ).all()

    # Calculate summary
    total_work_days = len(daily_work)

    completed_days = sum(
        1 for work in daily_work
        if work.office_out_time is not None
    )

    pending_days = total_work_days - completed_days

    latest_work_date = (
        daily_work[0].work_date
        if daily_work
        else None
    )

    # Get the logged-in user's team information
    team = None

    if current_user.team_id:
        team = db.query(Team).filter(
            Team.id == current_user.team_id
        ).first()

    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "team_id": current_user.team_id,
            "team_name": team.team_name if team else None
        },
        "summary": {
            "total_work_days": total_work_days,
            "completed_days": completed_days,
            "pending_days": pending_days,
            "latest_work_date": latest_work_date
        }
    }



# ============================================================
# 6. MEMBER - RECENT WORK
# ============================================================

@router.get("/dashboard/recent")
def get_recent_user_work(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    daily_work = db.query(DailyWork).filter(
        DailyWork.user_id == current_user.id
    ).order_by(
        DailyWork.work_date.desc()
    ).limit(5).all()

    result = []

    for work in daily_work:
        result.append({
            "daily_work_id": work.id,
            "work_date": work.work_date,
            "office_in_time": work.office_in_time,
            "working_points": work.working_points,
            "office_out_time": work.office_out_time,
            "points_completed": work.points_completed,
            "pending_points": work.pending_points,
            "morning_message": work.morning_message,
            "evening_message": work.evening_message
        })

    return {
        "total_records": len(result),
        "recent_work": result
    }


# ============================================================
# 7. MEMBER - DASHBOARD BY DATE
# ============================================================

@router.get("/dashboard/date/{work_date}")
def get_user_dashboard_by_date(
    work_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    work = db.query(DailyWork).filter(
        DailyWork.user_id == current_user.id,
        DailyWork.work_date == work_date
    ).first()

    if not work:
        raise HTTPException(
            status_code=404,
            detail="No daily work found for this date"
        )

    return {
        "daily_work_id": work.id,
        "user_id": work.user_id,
        "work_date": work.work_date,
        "office_in_time": work.office_in_time,
        "working_points": work.working_points,
        "office_out_time": work.office_out_time,
        "points_completed": work.points_completed,
        "pending_points": work.pending_points,
        "morning_message": work.morning_message,
        "evening_message": work.evening_message
    }


# ============================================================
# 8. TEAM_ADMIN - TEAM DAILY WORK
# ============================================================
# ============================================================
# 8. GET TEAM DAILY WORK
# GET /daily-work/team
#
# TEAM_ADMIN  -> assigned teams only
# SUPER_ADMIN -> all teams
# MEMBER      -> not allowed
# ============================================================


@router.get("/team")
def get_team_daily_work(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # -----------------------------------------
    # SUPER_ADMIN
    # -----------------------------------------
    if current_user.role == "SUPER_ADMIN":

        users = db.query(User).filter(
            User.role.in_(["MEMBER", "TEAM_ADMIN"]),
            User.is_activate == True
        ).all()

    # -----------------------------------------
    # TEAM_ADMIN
    # -----------------------------------------
    elif current_user.role == "TEAM_ADMIN":

        assignments = db.query(TeamAdmin).filter(
            TeamAdmin.user_id == current_user.id
        ).all()

        if not assignments:
            return {
                "message": "No teams assigned to this TEAM_ADMIN",
                "total_records": 0,
                "work": []
            }

        team_ids = [
            assignment.team_id
            for assignment in assignments
        ]

        users = db.query(User).filter(
            User.team_id.in_(team_ids),
            User.role == "MEMBER",
            User.is_activate == True
        ).all()

    # -----------------------------------------
    # MEMBER
    # -----------------------------------------
    else:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access team daily work"
        )

    # -----------------------------------------
    # No users found
    # -----------------------------------------
    if not users:
        return {
            "total_records": 0,
            "work": []
        }

    # -----------------------------------------
    # Get user IDs
    # -----------------------------------------
    user_ids = [
        user.id
        for user in users
    ]

    # -----------------------------------------
    # Get daily work
    # -----------------------------------------
    daily_work = db.query(DailyWork).filter(
        DailyWork.user_id.in_(user_ids)
    ).order_by(
        DailyWork.work_date.desc()
    ).all()

    # -----------------------------------------
    # Prepare response
    # -----------------------------------------
    result = []

    for work in daily_work:

        user = db.query(User).filter(
            User.id == work.user_id
        ).first()

        team = None

        if user and user.team_id:
            team = db.query(Team).filter(
                Team.id == user.team_id
            ).first()

        result.append({
            "daily_work_id": work.id,
            "user_id": work.user_id,
            "user_name": user.name if user else None,
            "user_email": user.email if user else None,
            "user_role": user.role if user else None,
            "team_id": user.team_id if user else None,
            "team_name": team.team_name if team else None,
            "work_date": work.work_date,
            "office_in_time": work.office_in_time,
            "working_points": work.working_points,
            "office_out_time": work.office_out_time,
            "points_completed": work.points_completed,
            "pending_points": work.pending_points,
            "morning_message": work.morning_message,
            "evening_message": work.evening_message,
            "created_at": work.created_at,
            "updated_at": work.updated_at
        })

    # -----------------------------------------
    # IMPORTANT: RETURN RESPONSE
    # -----------------------------------------
    return {
        "total_records": len(result),
        "work": result
    }
# ============================================================
# 9. GET TEAM DAILY WORK BY DATE
# GET /daily-work/team/date/{work_date}
#
# SUPER_ADMIN -> MEMBER + TEAM_ADMIN work from ALL teams
# TEAM_ADMIN  -> MEMBER work from assigned teams only
# MEMBER      -> Not allowed
# ============================================================

@router.get("/team/date/{work_date}")
def get_team_daily_work_by_date(
    work_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # ========================================================
    # SUPER_ADMIN
    # See MEMBER + TEAM_ADMIN work from ALL teams
    # for selected date
    # ========================================================

    if current_user.role == "SUPER_ADMIN":

        users = db.query(User).filter(
            User.role.in_(["MEMBER", "TEAM_ADMIN"]),
            User.is_activate == True
        ).all()

    # ========================================================
    # TEAM_ADMIN
    # See only MEMBER work from assigned teams
    # for selected date
    # ========================================================

    elif current_user.role == "TEAM_ADMIN":

        assignments = db.query(TeamAdmin).filter(
            TeamAdmin.user_id == current_user.id
        ).all()

        if not assignments:
            return {
                "message": "No teams assigned to this TEAM_ADMIN",
                "work_date": work_date,
                "total_records": 0,
                "daily_work": []
            }

        team_ids = [
            assignment.team_id
            for assignment in assignments
        ]

        users = db.query(User).filter(
            User.team_id.in_(team_ids),
            User.role == "MEMBER",
            User.is_activate == True
        ).all()

    # ========================================================
    # MEMBER
    # ========================================================

    else:

        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access team daily work"
        )

    # ========================================================
    # No users found
    # ========================================================

    if not users:
        return {
            "message": "No active users found",
            "work_date": work_date,
            "total_records": 0,
            "daily_work": []
        }

    # ========================================================
    # Get user IDs
    # ========================================================

    user_ids = [
        user.id
        for user in users
    ]

    # ========================================================
    # Get daily work for selected date
    # ========================================================

    daily_work = db.query(DailyWork).filter(
        DailyWork.user_id.in_(user_ids),
        DailyWork.work_date == work_date
    ).all()

    # ========================================================
    # Prepare response
    # ========================================================

    result = []

    for work in daily_work:

        user = db.query(User).filter(
            User.id == work.user_id
        ).first()

        team = None

        if user and user.team_id:
            team = db.query(Team).filter(
                Team.id == user.team_id
            ).first()

        result.append({
            "daily_work_id": work.id,

            "user_id": work.user_id,
            "user_name": user.name if user else None,
            "user_email": user.email if user else None,
            "user_role": user.role if user else None,

            "team_id": user.team_id if user else None,
            "team_name": team.team_name if team else None,

            "work_date": work.work_date,

            "office_in_time": work.office_in_time,
            "working_points": work.working_points,

            "office_out_time": work.office_out_time,
            "points_completed": work.points_completed,
            "pending_points": work.pending_points,

            "morning_message": work.morning_message,
            "evening_message": work.evening_message,

            "created_at": work.created_at,
            "updated_at": work.updated_at
        })

    return {
        "work_date": work_date,
        "total_records": len(result),
        "daily_work": result
    }

# ============================================================
# 10. SUPER_ADMIN - ALL DAILY WORK
# ============================================================


@router.get("/admin")
def get_all_daily_work(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check SUPER_ADMIN permission
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only SUPER_ADMIN can access all daily work"
        )

    # Get all daily work records
    daily_work = db.query(DailyWork).order_by(
        DailyWork.work_date.desc()
    ).all()

    result = []

    for work in daily_work:
        # Get the user who submitted this work
        user = db.query(User).filter(
            User.id == work.user_id
        ).first()

        # Get the user's team
        team = None
        if user and user.team_id:
            team = db.query(Team).filter(
                Team.id == user.team_id
            ).first()

        result.append({
            "daily_work_id": work.id,
            "user_id": work.user_id,
            "user_name": user.name if user else None,
            "user_email": user.email if user else None,
            "user_role": user.role if user else None,
            "team_id": user.team_id if user else None,
            "team_name": team.team_name if team else None,
            "work_date": work.work_date,
            "office_in_time": work.office_in_time,
            "working_points": work.working_points,
            "office_out_time": work.office_out_time,
            "points_completed": work.points_completed,
            "pending_points": work.pending_points,
            "morning_message": work.morning_message,
            "evening_message": work.evening_message,
            "created_at": work.created_at,
            "updated_at": work.updated_at
        })

    return {
        "total_records": len(result),
        "daily_work": result
    }


# ============================================================
# 10.7 SUPER_ADMIN OVERALL SUMMARY
# GET /daily-work/admin/summary
#
# SUPER_ADMIN only
# ============================================================

@router.get("/admin/summary")
def get_admin_overall_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Check SUPER_ADMIN permission
    # --------------------------------------------------------

    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only SUPER_ADMIN can access overall summary"
        )

    # --------------------------------------------------------
    # 1. TEAM SUMMARY
    # --------------------------------------------------------

    total_teams = db.query(Team).count()

    active_teams = db.query(Team).filter(
        Team.is_activate == True
    ).count()

    inactive_teams = total_teams - active_teams

    # --------------------------------------------------------
    # 2. USER SUMMARY
    # --------------------------------------------------------

    total_users = db.query(User).count()

    active_users = db.query(User).filter(
        User.is_activate == True
    ).count()

    inactive_users = total_users - active_users

    # --------------------------------------------------------
    # 3. ROLE-WISE USER SUMMARY
    # --------------------------------------------------------

    total_members = db.query(User).filter(
        User.role == "MEMBER"
    ).count()

    total_team_admins = db.query(User).filter(
        User.role == "TEAM_ADMIN"
    ).count()

    total_super_admins = db.query(User).filter(
        User.role == "SUPER_ADMIN"
    ).count()

    # --------------------------------------------------------
    # 4. DAILY WORK SUMMARY
    # --------------------------------------------------------

    total_work_records = db.query(DailyWork).count()

    completed_days = db.query(DailyWork).filter(
        DailyWork.office_out_time.isnot(None)
    ).count()

    pending_days = db.query(DailyWork).filter(
        DailyWork.office_out_time.is_(None)
    ).count()

    # --------------------------------------------------------
    # 5. LATEST WORK DATE
    # --------------------------------------------------------

    latest_work = db.query(DailyWork).order_by(
        DailyWork.work_date.desc()
    ).first()

    latest_work_date = (
        latest_work.work_date
        if latest_work
        else None
    )

    # --------------------------------------------------------
    # 6. RETURN OVERALL SUMMARY
    # --------------------------------------------------------

    return {
        "message": "SUPER_ADMIN overall summary retrieved successfully",

        "teams": {
            "total_teams": total_teams,
            "active_teams": active_teams,
            "inactive_teams": inactive_teams
        },

        "users": {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users
        },

        "roles": {
            "total_members": total_members,
            "total_team_admins": total_team_admins,
            "total_super_admins": total_super_admins
        },

        "daily_work": {
            "total_work_records": total_work_records,
            "completed_days": completed_days,
            "pending_days": pending_days,
            "latest_work_date": latest_work_date
        }
    }

# ============================================================
# 10.8 SUPER_ADMIN TEAM SUMMARY
# GET /daily-work/admin/team-summary
#
# SUPER_ADMIN only
# Shows summary for every team
# Includes MEMBER + TEAM_ADMIN work
# ============================================================

@router.get("/admin/team-summary")
def get_admin_team_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Check SUPER_ADMIN permission
    # --------------------------------------------------------

    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only SUPER_ADMIN can access team summary"
        )

    # --------------------------------------------------------
    # Get all teams
    # --------------------------------------------------------

    teams = db.query(Team).all()

    result = []

    # --------------------------------------------------------
    # Process each team
    # --------------------------------------------------------

    for team in teams:

        # ----------------------------------------------------
        # Get active MEMBERS
        # ----------------------------------------------------

        members = db.query(User).filter(
            User.team_id == team.id,
            User.role == "MEMBER",
            User.is_activate == True
        ).all()

        # ----------------------------------------------------
        # Get active TEAM_ADMINs
        # ----------------------------------------------------

        team_admins = db.query(User).filter(
            User.team_id == team.id,
            User.role == "TEAM_ADMIN",
            User.is_activate == True
        ).all()

        # ----------------------------------------------------
        # Get all active MEMBER + TEAM_ADMIN users
        # ----------------------------------------------------

        users = db.query(User).filter(
            User.team_id == team.id,
            User.role.in_(["MEMBER", "TEAM_ADMIN"]),
            User.is_activate == True
        ).all()

        user_ids = [
            user.id
            for user in users
        ]

        # ----------------------------------------------------
        # Get daily work for this team
        # ----------------------------------------------------

        daily_work = []

        if user_ids:

            daily_work = db.query(DailyWork).filter(
                DailyWork.user_id.in_(user_ids)
            ).all()

        # ----------------------------------------------------
        # Work statistics
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Team result
        # ----------------------------------------------------

        result.append({
            "team_id": team.id,
            "team_name": team.team_name,
            "academic_year": team.academic_year,
            "is_activate": team.is_activate,

            "total_members": len(members),
            "total_team_admins": len(team_admins),

            "total_work_records": total_work_records,
            "completed_days": completed_days,
            "pending_days": pending_days
        })

    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    return {
        "message": "SUPER_ADMIN team summary retrieved successfully",
        "total_teams": len(result),
        "teams": result
    }

@router.get("/admin/user/{user_id}")
def get_admin_user_wise_work(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only SUPER_ADMIN can access this
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only SUPER_ADMIN can access user-wise work"
        )

    # Find the user
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Find user's team
    team = None

    if user.team_id:
        team = db.query(Team).filter(
            Team.id == user.team_id
        ).first()

    # Get all daily work of this user
    daily_work = db.query(DailyWork).filter(
        DailyWork.user_id == user.id
    ).order_by(
        DailyWork.work_date.desc()
    ).all()

    result = []

    for work in daily_work:
        result.append({
            "daily_work_id": work.id,
            "user_id": user.id,
            "user_name": user.name,
            "user_email": user.email,
            "user_role": user.role,
            "team_id": user.team_id,
            "team_name": team.team_name if team else None,
            "work_date": work.work_date,
            "office_in_time": work.office_in_time,
            "working_points": work.working_points,
            "office_out_time": work.office_out_time,
            "points_completed": work.points_completed,
            "pending_points": work.pending_points,
            "morning_message": work.morning_message,
            "evening_message": work.evening_message,
            "created_at": work.created_at,
            "updated_at": work.updated_at
        })

    return {
        "message": "SUPER_ADMIN user-wise work retrieved successfully",
        "user": {
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "team_id": user.team_id,
            "team_name": team.team_name if team else None,
            "is_activate": user.is_activate
        },
        "total_records": len(result),
        "work": result
    }

# ============================================================
# 3. REQUEST HISTORICAL WORK EDIT
# ============================================================

@router.post("/historical-edit-request")
def create_historical_edit_request(
    request_data: HistoricalEditRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only MEMBER and TEAM_ADMIN can request historical edits
    if current_user.role != "MEMBER":
        raise HTTPException(
        status_code=403,
        detail="Only members can submit historical edit requests. "
               "TEAM_ADMIN must request edits for their own work through "
               "the appropriate self-service workflow."
    )

    # Find the requested work record
    daily_work = db.query(DailyWork).filter(
        DailyWork.id == request_data.daily_work_id
    ).first()

    if not daily_work:
        raise HTTPException(
            status_code=404,
            detail="Daily work record not found."
        )

    # Members can request edits only for their own work
    if current_user.role == "MEMBER":
        if daily_work.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can request edits only for your own work."
            )

    # TEAM_ADMIN can request edits only for work belonging
    # to their assigned teams
    elif current_user.role == "TEAM_ADMIN":
        work_owner = db.query(User).filter(
            User.id == daily_work.user_id
        ).first()

        if not work_owner or not work_owner.team_id:
            raise HTTPException(
                status_code=403,
                detail="The work owner does not belong to a team."
            )

        assignment = db.query(TeamAdmin).filter(
            TeamAdmin.user_id == current_user.id,
            TeamAdmin.team_id == work_owner.team_id
        ).first()

        if not assignment:
            raise HTTPException(
                status_code=403,
                detail="You can request edits only for work in your assigned teams."
            )

    # Work must be historical, not today's work
    today = get_today_date()

    if daily_work.work_date >= today:
        raise HTTPException(
            status_code=400,
            detail="Historical edit requests are allowed only for previous dates."
        )

    # Prevent duplicate pending requests for the same work record
    existing_request = db.query(HistoricalEditRequest).filter(
        HistoricalEditRequest.daily_work_id == daily_work.id,
        HistoricalEditRequest.requested_by == current_user.id,
        HistoricalEditRequest.status == "PENDING"
    ).first()

    if existing_request:
        raise HTTPException(
            status_code=409,
            detail="A pending historical edit request already exists."
        )

    # Create the request
    new_request = HistoricalEditRequest(
        daily_work_id=daily_work.id,
        requested_by=current_user.id,
        request_reason=request_data.request_reason.strip(),
        status="PENDING",
        requested_at=datetime.now()
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return {
        "message": "Historical edit request submitted successfully.",
        "request_id": new_request.id,
        "daily_work_id": new_request.daily_work_id,
        "requested_by": new_request.requested_by,
        "status": new_request.status,
        "requested_at": new_request.requested_at
    }



@router.put("/historical-edit-request/{request_id}/review")
def review_historical_edit_request(
    request_id: int,
    review_data: HistoricalEditRequestReview,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only TEAM_ADMIN and SUPER_ADMIN can review requests
    if current_user.role not in ["TEAM_ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to review historical edit requests."
        )

    # Find the historical edit request
    edit_request = db.query(HistoricalEditRequest).filter(
        HistoricalEditRequest.id == request_id
    ).first()

    if not edit_request:
        raise HTTPException(
            status_code=404,
            detail="Historical edit request not found."
        )

    # A request can be reviewed only once
    if edit_request.status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail="This request has already been reviewed."
        )

    # Find the associated daily work record
    daily_work = db.query(DailyWork).filter(
        DailyWork.id == edit_request.daily_work_id
    ).first()

    if not daily_work:
        raise HTTPException(
            status_code=404,
            detail="Associated daily work record not found."
        )

    # Find the person who submitted the request
    requester = db.query(User).filter(
        User.id == edit_request.requested_by
    ).first()

    if not requester:
        raise HTTPException(
            status_code=404,
            detail="Requesting user not found."
        )

    # MEMBER requests can be reviewed by SUPER_ADMIN
    # or by their assigned TEAM_ADMIN
    if requester.role == "MEMBER":

        if current_user.role == "SUPER_ADMIN":
            # SUPER_ADMIN can review requests from any team
            pass

        elif current_user.role == "TEAM_ADMIN":

            if not requester.team_id:
                raise HTTPException(
                    status_code=403,
                    detail="The requesting member is not assigned to a team."
                )

            assignment = db.query(TeamAdmin).filter(
                TeamAdmin.user_id == current_user.id,
                TeamAdmin.team_id == requester.team_id
            ).first()

            if not assignment:
                raise HTTPException(
                    status_code=403,
                    detail="You are not the assigned TEAM_ADMIN for this member's team."
                )

    # TEAM_ADMIN requests must be reviewed by SUPER_ADMIN
    elif requester.role == "TEAM_ADMIN":

        if current_user.role != "SUPER_ADMIN":
            raise HTTPException(
                status_code=403,
                detail="TEAM_ADMIN requests must be reviewed by SUPER_ADMIN."
            )

    else:
        raise HTTPException(
            status_code=400,
            detail="This request was not submitted by a MEMBER or TEAM_ADMIN."
        )

    # Update review details
    edit_request.status = review_data.status
    edit_request.reviewed_by = current_user.id
    edit_request.review_comment = (
        review_data.review_comment.strip()
        if review_data.review_comment
        else None
    )
    edit_request.reviewed_at = datetime.now()

    db.commit()
    db.refresh(edit_request)

    return {
        "message": (
            f"Historical edit request "
            f"{edit_request.status.lower()} successfully."
        ),
        "request_id": edit_request.id,
        "daily_work_id": edit_request.daily_work_id,
        "status": edit_request.status,
        "reviewed_by": edit_request.reviewed_by,
        "review_comment": edit_request.review_comment,
        "reviewed_at": edit_request.reviewed_at
    }


@router.get("/historical-edit-requests")
def get_historical_edit_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = (
        db.query(HistoricalEditRequest, DailyWork, User)
        .join(
            DailyWork,
            HistoricalEditRequest.daily_work_id == DailyWork.id
        )
        .join(
            User,
            HistoricalEditRequest.requested_by == User.id
        )
    )

    # MEMBER: view only their own requests
    if current_user.role == "MEMBER":
        query = query.filter(
            HistoricalEditRequest.requested_by == current_user.id
        )

    # TEAM_ADMIN: view requests from members in assigned teams
    elif current_user.role == "TEAM_ADMIN":
        assignments = db.query(TeamAdmin).filter(
            TeamAdmin.user_id == current_user.id
        ).all()

        team_ids = [item.team_id for item in assignments]

        if not team_ids:
            return {
                "total_records": 0,
                "requests": []
            }

        query = query.filter(
            User.team_id.in_(team_ids),
            User.role == "MEMBER"
        )

    # SUPER_ADMIN: view all requests
    elif current_user.role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to view historical edit requests."
        )

    records = query.order_by(
        HistoricalEditRequest.requested_at.desc()
    ).all()

    requests = []

    for edit_request, work, requester in records:
        reviewer = None

        if edit_request.reviewed_by is not None:
            reviewer = db.query(User).filter(
                User.id == edit_request.reviewed_by
            ).first()

        team = None

        if requester.team_id:
            team = db.query(Team).filter(
                Team.id == requester.team_id
            ).first()

        requests.append({
            "request_id": edit_request.id,
            "daily_work_id": edit_request.daily_work_id,
            "work_date": work.work_date,
            "work_owner_id": work.user_id,
            "requester_id": requester.id,
            "requester_name": requester.name,
            "requester_role": requester.role,
            "team_id": requester.team_id,
            "team_name": team.team_name if team else None,
            "request_reason": edit_request.request_reason,
            "status": edit_request.status,
            "reviewed_by": edit_request.reviewed_by,
            "reviewer_name": reviewer.name if reviewer else None,
            "review_comment": edit_request.review_comment,
            "requested_at": edit_request.requested_at,
            "reviewed_at": edit_request.reviewed_at,
            "used_at": edit_request.used_at
        })

    return {
        "total_records": len(requests),
        "requests": requests
    }


@router.put("/historical-work/{daily_work_id}/edit")
def edit_historical_work(
    daily_work_id: int,
    edit_data: HistoricalWorkEdit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find the historical work record
    daily_work = db.query(DailyWork).filter(
        DailyWork.id == daily_work_id
    ).first()

    if not daily_work:
        raise HTTPException(
            status_code=404,
            detail="Daily work record not found."
        )

    # Only allow edits to previous dates
    today = get_today_date()

    if daily_work.work_date >= today:
        raise HTTPException(
            status_code=400,
            detail="This endpoint is only for historical work."
        )

    # Find an approved request for this work record
    approved_request = db.query(HistoricalEditRequest).filter(
        HistoricalEditRequest.daily_work_id == daily_work_id,
        HistoricalEditRequest.status == "APPROVED"
    ).order_by(
        HistoricalEditRequest.reviewed_at.desc()
    ).first()

    if not approved_request:
        raise HTTPException(
            status_code=403,
            detail="An approved historical edit request is required."
        )

    if approved_request.used_at is not None:
        raise HTTPException(
            status_code=409,
            detail="This approved request has already been used."
    )

    
    # Verify the editor is the member who requested the approval
    if current_user.role != "MEMBER":
        raise HTTPException(
            status_code=403,
            detail="Only members can edit their own historical work."
        )

    if current_user.id != daily_work.user_id:
        raise HTTPException(
            status_code=403,
            detail="You can edit only your own historical work."
        )

    if approved_request.requested_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can edit only work covered by your own approved request."
        )


    
    # Update only fields supplied by the caller
    update_data = edit_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one field to update."
        )

    # Capture original values before changing anything
    old_values = {}

    for field in update_data:
        old_value = getattr(daily_work, field)

        if isinstance(old_value, (datetime, date)):
            old_values[field] = old_value.isoformat()
        elif hasattr(old_value, "isoformat"):
            old_values[field] = old_value.isoformat()
        else:
            old_values[field] = old_value

    # Apply the requested changes
    for field, value in update_data.items():
        setattr(daily_work, field, value)

    daily_work.updated_at = datetime.now()

    # Capture the updated values
    new_values = {}

    for field in update_data:
        new_value = getattr(daily_work, field)

        if isinstance(new_value, (datetime, date)):
            new_values[field] = new_value.isoformat()
        elif hasattr(new_value, "isoformat"):
            new_values[field] = new_value.isoformat()
        else:
            new_values[field] = new_value

    # Create the audit record
    audit_record = HistoricalWorkEditAudit(
        daily_work_id=daily_work.id,
        edit_request_id=approved_request.id,
        edited_by=current_user.id,
        old_values=json.dumps(old_values),
        new_values=json.dumps(new_values),
        edited_at=datetime.now()
    )

    db.add(audit_record)

    approved_request.used_at = datetime.now()

    # Save the work update and audit record together
    try:
        db.commit()
        db.refresh(daily_work)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save the historical edit and audit record."
        )

    return {
        "message": "Historical work updated successfully.",
        "daily_work_id": daily_work.id,
        "work_date": daily_work.work_date,
        "updated_by": current_user.id,
        "updated_at": daily_work.updated_at
    }

# ============================================================
# 11. HISTORICAL WORK EDIT AUDIT LOGS
# GET /daily-work/historical-work-audit
# SUPER_ADMIN: all audit logs
# TEAM_ADMIN: logs for members in assigned teams
# MEMBER: not allowed
# ============================================================

@router.get("/historical-work-audit")
def get_historical_work_edit_audit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only administrators can view historical edit audit logs.
    if current_user.role not in ["TEAM_ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Only TEAM_ADMIN or SUPER_ADMIN can view historical edit audit logs."
        )

    query = (
        db.query(HistoricalWorkEditAudit, DailyWork, User)
        .join(DailyWork, HistoricalWorkEditAudit.daily_work_id == DailyWork.id)
        .join(User, DailyWork.user_id == User.id)
    )

    if current_user.role == "TEAM_ADMIN":
        assignments = db.query(TeamAdmin).filter(
            TeamAdmin.user_id == current_user.id
        ).all()

        team_ids = [assignment.team_id for assignment in assignments]

        if not team_ids:
            return {"total_records": 0, "audit_logs": []}

        query = query.filter(User.team_id.in_(team_ids), User.role == "MEMBER")

    records = query.order_by(
        HistoricalWorkEditAudit.edited_at.desc()
    ).all()

    audit_logs = []
    for audit, work, editor_work_owner in records:
        editor = db.query(User).filter(
            User.id == audit.edited_by
        ).first()

        team = None

        if editor_work_owner.team_id:
            team = db.query(Team).filter(
                Team.id == editor_work_owner.team_id
            ).first()

        edit_request = db.query(HistoricalEditRequest).filter(
            HistoricalEditRequest.id == audit.edit_request_id
        ).first()
        reviewer = None
        if edit_request and edit_request.reviewed_by is not None:
            reviewer = db.query(User).filter(
                User.id == edit_request.reviewed_by
            ).first()

        audit_logs.append({
            "audit_id": audit.id,
            "daily_work_id": audit.daily_work_id,
            "work_date": work.work_date,
            "work_owner_id": editor_work_owner.id,
            "work_owner_name": editor_work_owner.name,
            "team_id": editor_work_owner.team_id,
            "team_name": team.team_name if team else None,
            "edit_request_id": audit.edit_request_id,
            "requested_by": edit_request.requested_by if edit_request else None,
            "reviewed_by": edit_request.reviewed_by if edit_request else None,
            "reviewer_name": reviewer.name if reviewer else None,
            "edited_by": audit.edited_by,
            "editor_name": editor.name if editor else None,
            "old_values": json.loads(audit.old_values),
            "new_values": json.loads(audit.new_values),
            "edited_at": audit.edited_at
        })

    return {
        "total_records": len(audit_logs),
        "audit_logs": audit_logs
    }
