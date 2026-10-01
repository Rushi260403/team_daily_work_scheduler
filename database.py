import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base


# Load .env file
load_dotenv()


# Read database details
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")


# SQL Server connection string
connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_DATABASE};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)


# Create SQLAlchemy URL
DATABASE_URL = URL.create(
    "mssql+pyodbc",
    query={
        "odbc_connect": connection_string
    }
)


# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=True
)


# Create database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Base class for SQLAlchemy models
Base = declarative_base()


# Database dependency
def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()