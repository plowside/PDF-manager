from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import time

from .models import *
from .. import db_api


#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "317aef2b141c92168b99303376221476e9130e9dff7e8ad27b00c95dd85ad00d"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440


def get_password_hash(password):
	return pwd_context.hash(password, salt=SECRET_KEY[:22])

def verify_password(plain_password, hashed_password):
	return pwd_context.verify(plain_password, hashed_password)



def create_jwt_token(data: dict, expire_delta: timedelta):
	to_encode = data.copy()
	expire = int((datetime.utcnow() + expire_delta).timestamp())

	to_encode.update({"expire": expire})
	return {'token': jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM), 'expire': expire}

async def auth_user(user_auth: UserAuth):
	_db = db_api.database_driver()
	con, cur = _db._get_connection()

	user = await _db.get_user(user_auth)
	if not user:
		return {'error': True, 'error_code': 401, 'message': 'Incorrect username or password'}
	user = UserInDB(**dict(user))
	if not verify_password(user_auth.password, user.hashed_password):
		return {'error': True, 'error_code': 401, 'message': 'Incorrect username or password'}

	access_token = create_jwt_token(data={'uid': user.uid, 'access_level': user.access_level, 'hashed_password': user.hashed_password}, expire_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


	return {'error': False, 'user': UserInDB(**dict(user)), 'response': {'error': False, 'access_token': access_token['token'], 'token_type': 'Bearer', 'expire_at': access_token['expire']}}

async def create_user(user_create: UserCreate):
	_db = db_api.database_driver()
	con, cur = _db._get_connection()

	user = await _db.get_user(UserAuth(**dict(user_create)))
	if user:
		return {'error': True, 'error_code': 200, 'message': 'Username already exists'}
	user_create.password = get_password_hash(user_create.password)
	user = UserInDB(**dict(await _db.create_user(user_create)))

	access_token = create_jwt_token(data={'uid': user.uid, 'access_level': user.access_level, 'hashed_password': user.hashed_password}, expire_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


	return {'error': False, 'user': UserInDB(**dict(user)), 'response': {'error': False, 'access_token': access_token['token'], 'token_type': 'Bearer', 'expire_at': access_token['expire']}}

def auth_check(token):
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		
		if payload.get('expire') < int(time.time()):
			return {'error': True, 'message': 'Authorization token expired'}
	except:
		return None

	user = JWTTokenPayload(**payload)
	return user