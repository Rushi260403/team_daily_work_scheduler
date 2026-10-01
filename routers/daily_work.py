from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import DailyWork, User, TeamAdmin, Team
from schemas import (
    MorningWorkCreate,
    EveningWorkUpdate
)
from dependencies.auth import get_current_user


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

    # Check whether work already exists for this date
    existing_work = db.query(DailyWork).filter(
        DailyWork.user_id == current_user.id,
        DailyWork.work_date == work_data.work_date
    ).first()

    if existing_work:
        raise HTTPException(
            status_code=400,
            detail="Daily work already exists for this date"
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

    existing_work = db.query(DailyWork).filter(
        DailyWork.user_id == current_user.id,
        DailyWork.work_date == work_date
    ).first()

    if not existing_work:
        raise HTTPException(
            status_code=404,
            detail="Morning work not found for this date"
        )

    existing_work.office_out_time = work_data.office_out_time
    existing_work.points_completed = work_data.points_completed
    existing_work.pending_points = work_data.pending_points

    # Create evening message
    evening_message = (
        f"Date: {existing_work.work_date}. "
        f"Office Out Time: {work_data.office_out_time}. "
        f"Points Completed: {work_data.points_completed}. "
        f"Pending Points: {work_data.pending_points}"
    )

    existing_work.evening_message = evening_message
    existing_work.updated_at = datetime.now()

    db.commit()
    db.refresh(existing_work)

    return {
        "message": "Evening work saved successfully",
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

    # Get all work of logged-in user
    daily_work = db.query(DailyWork).filter(
        DailyWork.user_id == current_user.id
    ).order_by(
        DailyWork.work_date.desc()
    ).all()

    total_work_days = len(daily_work)

    completed_days = 0
    pending_days = 0

    for work in daily_work:

        # If evening work is submitted,
        # consider the day completed
        if work.office_out_time is not None:
            completed_days += 1
        else:
            pending_days += 1

    latest_work_date = None

    if daily_work:
        latest_work_date = daily_work[0].work_date

    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "team_id": current_user.team_id
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

        # Get user who submitted the work
        user = db.query(User).filter(
            User.id == work.user_id
        ).first()

        result.append({
            "daily_work_id": work.id,
            "user_id": work.user_id,
            "user_name": user.name if user else None,
            "user_email": user.email if user else None,
            "team_id": user.team_id if user else None,
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