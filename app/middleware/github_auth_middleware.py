from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import ExpiredSignatureError, InvalidTokenError

from app.utils.jwt_utils import decode_jwt_token

security = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    """
    FastAPI dependency that validates the JWT bearer token and
    returns the decoded payload containing user context.
    """
    token = credentials.credentials

    try:
        payload = decode_jwt_token(token)
        user_id = payload.get("user_id")
        github_id = payload.get("github_id")
        github_access_token = payload.get("github_access_token")

        if not all([user_id, github_id, github_access_token]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication payload",
            )

        return {
            "token": token,
            "user_id": user_id,
            "github_id": github_id,
            "github_access_token": github_access_token,
        }

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )