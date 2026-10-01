from database import SessionLocal

from models import (
    Team,
    User,
    TeamAdmin,
    DailyWork,
    UserSettings
)


db = SessionLocal()


try:

    print()
    print("===================================")
    print("Testing SQLAlchemy Models")
    print("===================================")

    # Test Teams
    teams = db.query(Team).all()

    print()
    print("Teams:")
    print("-----------------------------------")

    for team in teams:

        print(
            team.id,
            "|",
            team.team_name,
            "|",
            team.academic_year
        )


    # Test Users
    users = db.query(User).all()

    print()
    print("Users:")
    print("-----------------------------------")

    print("Total Users:", len(users))


    # Test Team Admins
    team_admins = db.query(TeamAdmin).all()

    print()
    print("Team Admins:")
    print("-----------------------------------")

    print("Total Team Admins:", len(team_admins))


    # Test Daily Work
    daily_work = db.query(DailyWork).all()

    print()
    print("Daily Work Records:")
    print("-----------------------------------")

    print("Total Daily Work Records:", len(daily_work))


    # Test User Settings
    user_settings = db.query(UserSettings).all()

    print()
    print("User Settings:")
    print("-----------------------------------")

    print("Total User Settings:", len(user_settings))


    print()
    print("===================================")
    print("All SQLAlchemy models tested!")
    print("===================================")


except Exception as e:

    print()
    print("===================================")
    print("Model test failed!")
    print("Error:", e)
    print("===================================")


finally:

    db.close()