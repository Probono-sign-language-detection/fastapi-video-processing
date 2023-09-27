from fastapi import Depends, HTTPException, APIRouter, status
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)


def get_access_token(
        auth_header: HTTPAuthorizationCredentials | None = Depends(
            HTTPBearer(auto_error=False)
        ),
) -> str:
    if auth_header is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
    return auth_header.credentials  # access_token
