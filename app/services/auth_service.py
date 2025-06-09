from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from config.database import get_database
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.db = get_database()
        self.user_collection = self.db.user
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.jwt_secret = settings.JWT_SECRET
        self.jwt_algorithm = 'HS256'
        self.token_expire_hours = int(settings.JWT_EXPIRATION[:-1])  # Assuming JWT_EXPIRATION is like "1h"

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and return JWT token with user data
        """
        try:
            if not email or not password:
                raise ValueError("email and password are required")
            # Query the database for user 
            user = self.user_collection.find_one({"email": email})
          
            if not user:
                raise ValueError("User not found")

            # Verify password
            if not self.pwd_context.verify(password, user['password_hash']):
                raise ValueError("Invalid credentials")            
            # Create JWT payload
            payload = {
                'id': str(user['_id']),
                'user_id': user['user_id'],
                'role': user['role'],
                'exp': datetime.utcnow() + timedelta(hours=self.token_expire_hours)
            }

            # Generate JWT token
            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

            # Prepare user data response
            user_data = {
                'id': str(user['_id']),
                'user_id': user['user_id'],
                'username': user['username'],
                'role': user['role']
            }

            return {
                'message': 'Login successful',
                'token': token,
                'user': user_data
            }

        except ValueError as e:
            logger.error(f'Login validation error: {e}')
            raise
        except Exception as e:
            logger.error(f'Login error: {e}')
            raise Exception(f"Internal server error: {str(e)}")

    # def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
    #     """
    #     Verify JWT token and return payload if valid
    #     """
    #     try:
    #         payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
    #         # Check if token is expired
    #         exp_timestamp = payload.get('exp')
    #         if exp_timestamp:
    #             exp_datetime = datetime.fromtimestamp(exp_timestamp)
    #             if datetime.utcnow() > exp_datetime:
    #                 return False  # Token is expired
            
    #         return payload
    #     except JWTError as e:
    #         logger.warning(f'JWT verification failed: {e}')
    #         return False
    #     except Exception as e:
    #         logger.error(f'Token verification error: {e}')
    #         return False

   


