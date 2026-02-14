from fastapi import Depends, HTTPException, status
from app.auth.jwt import decode_jwt
from app.schemas.auth import UserContext
from app.core.logging import logger
from app.db.base import Base


from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.auth import UserContext

security = HTTPBearer()
# def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security),
# ) -> UserContext:
#     token = credentials.credentials
#     payload = decode_jwt(token)

#     if "user_id" not in payload or "role" not in payload:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token payload"
#         )

#     return UserContext(
#         user_id=payload["user_id"],
#         role=payload["role"],
#         department=payload.get("department"),
#     )



def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserContext:
    token = credentials.credentials
    payload = decode_jwt(token)

    if "user_id" not in payload or "role" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    return UserContext(
        user_id=payload["user_id"],
        role=payload["role"],
        department=payload.get("department"),
    )

