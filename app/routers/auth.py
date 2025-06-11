from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from services.auth_service import AuthService

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str


def get_auth_service() -> AuthService:
    return AuthService()

@router.post("/login")
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        result = await auth_service.login(request.email, request.password)
        return result
    except ValueError as e:
        if "User not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "Invalid credentials" in str(e):
            raise HTTPException(status_code=401, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.post("/logout")
# async def logout(
#     request: LogoutRequest,
#     auth_service: AuthService = Depends(get_auth_service)
# ):
#     """
#     Logout user (mainly for logging purposes in stateless JWT)
#     """
#     try:
#         result = await auth_service.logout(request.token)
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/verify")
# async def verify_token(
#     current_user: Dict[str, Any] = Depends(get_current_user),
#     auth_service: AuthService = Depends(get_auth_service)
# ):
#     """
#     Verify if current JWT token is valid and not expired
#     """
#     return {
#         "valid": True,
#         "expired": False,
#         "user_data": current_user
#     }
