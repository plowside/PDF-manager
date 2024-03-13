from pydantic import BaseModel

class UserAuth(BaseModel):
	username: str
	password: str

class UserCreate(BaseModel):
	access_hash: str | None = None
	username: str
	password: str
	access_level: int | None = 1

class UserInDB(BaseModel):
	uid: int
	username: str
	hashed_password: str
	access_level: int

class JWTTokenPayload(BaseModel):
	uid: int
	hashed_password: str
	access_level: int | None = 1
	expire: int | None = None


class FiltersGet(BaseModel):
	fields: dict | None = {}
	full_comparasion: bool | None = True
	all_records: bool | None = False
