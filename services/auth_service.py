import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import jwt

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM","HS256")

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES","60")
)

def create_access_token(user_id: int, email: str, role: str):
    expire_time = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": expire_time
    }

    token = jwt.encode(
        payload,
        JWT_SECRET_KEY, # type: ignore
        algorithm=JWT_ALGORITHM
    )

    return token