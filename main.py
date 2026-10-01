from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from database import engine
from routers.users import router as users_router
from routers.teams import router as teams_router
from routers.team_admins import router as team_admins_router
from routers.daily_work import router as daily_work_router

app = FastAPI(
    title="Team Daily Work Scheduler",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(teams_router)
app.include_router(team_admins_router)
app.include_router(daily_work_router)
@app.get("/")
def home():
    return{
        "message":"Team Daily Work Scheduler is running"
    }

@app.get("/test-db")
def test_database():
    try:
        with engine.connect() as connection:

            result = connection.execute(
                text("SELECT DB_NAME()")
            )

            database_name = result.scalar()

            return{
                "status":"success",
                "message":"Database connection successful",
                "server":"RUSHI\\SQLEXPRESS",
                "database":database_name
            }

    except Exception as e:

        return{
            "status":"failed",
            "message":"Database connection failed",
            "error":str(e)
        }

    