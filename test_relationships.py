from sqlalchemy import inspect

from database import engine


print()
print("===================================")
print("Testing Foreign Keys")
print("===================================")

inspector = inspect(engine)

tables = [
    "users",
    "team_admins",
    "daily_work",
    "user_settings"
]

for table_name in tables:

    print()
    print("Table:", table_name)
    print("-----------------------------------")

    foreign_keys = inspector.get_foreign_keys(table_name)

    if not foreign_keys:
        print("No foreign keys found.")
        continue

    for fk in foreign_keys:

        print(
            "Foreign Key:",
            fk["name"]
        )

        print(
            "Column:",
            fk["constrained_columns"]
        )

        print(
            "References:",
            fk["referred_table"],
            fk["referred_columns"]
        )


print()
print("===================================")
print("Foreign Key Test Completed!")
print("===================================")