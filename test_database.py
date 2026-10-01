from sqlalchemy import text

from database import engine


try:

    with engine.connect() as connection:

        result = connection.execute(
            text("SELECT DB_NAME()")
        )

        database_name = result.scalar()

        print()
        print("===================================")
        print("Database connection successful!")
        print("Connected Database:", database_name)
        print("===================================")


except Exception as e:

    print()
    print("===================================")
    print("Database connection failed!")
    print("Error:", e)
    print("===================================")