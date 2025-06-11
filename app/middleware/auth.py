from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional, Dict, Any
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

class AuthMiddleware:
    def __init__(self):
        self.jwt_secret = settings.JWT_SECRET
        self.jwt_algorithm = 'HS256'

    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning('Token has expired')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired!",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError:
            logger.warning('Invalid token')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token!",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            logger.error(f'Token verification error: {e}')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed",
                headers={"WWW-Authenticate": "Bearer"}
            )

    def check_role_permission(self, token_payload: Dict[str, Any], required_role: str) -> bool:
        try:
            user_role = token_payload.get('role')
            if not user_role:
                logger.warning('No role found in token payload')
                return False
            
            # Direct role comparison
            if user_role == required_role:
                return True
                        
        except Exception as e:
            logger.error(f'Role permission check error: {e}')
            return False


auth_middleware = AuthMiddleware()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    token = credentials.credentials
    payload = auth_middleware.verify_jwt_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

def require_role(required_role: str):
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if not auth_middleware.check_role_permission(current_user, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}",
            )
        return current_user
    
    return role_checker

def require_any_role(required_roles: list):
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_has_permission = any(
            auth_middleware.check_role_permission(current_user, role) 
            for role in required_roles
        )
        
        if not user_has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}",
            )
        return current_user
    
    return role_checker

require_admin = require_role("admin")
require_institution = require_role("institution")
access_both = require_any_role(["admin", "institution"])