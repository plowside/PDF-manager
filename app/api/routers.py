from fastapi import APIRouter, UploadFile, Response, Request, Cookie, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from typing import Optional

import shutil, hashlib, json

from .. import db_api
from .models import *
from .auth import *




router = APIRouter(prefix='/api', tags=['api'])

@router.post('/filter')
async def filters(payload: FiltersGet, Authorization: str = Cookie(None)):
	user = auth_check(Authorization)
	if not user: return RedirectResponse(url='/')
	elif user.access_level == 0:
		return []

	_db = db_api.database_driver()
	con, cur = _db._get_connection()

	results = await _db.get_records(fields=payload.fields, full_comparasion=payload.full_comparasion, all_records=payload.all_records)
	
	return results

@router.post('/add_record')
async def add_record(request: Request, Authorization: str = Cookie(None)):
	user = auth_check(Authorization)
	if not user: return RedirectResponse(url='/')
	elif user.access_level < 2:
		return {'error': 'You have no access to do that.'}

	async with request.form() as form:
		try:
			file = form["file"]
			record_data = FiltersGet(**json.loads(form["record_data"]))
		except: raise HTTPException(status_code=422, detail="Missing data")

		_db = db_api.database_driver()
		con, cur = _db._get_connection()

		record = await _db.add_record(1, record_data.fields, file)

	return record

@router.delete('/record/{record_id}')
async def delete_record(request: Request, record_id: int, Authorization: str = Cookie(None)):
	user = auth_check(Authorization)
	if not user: return RedirectResponse(url='/')
	elif user.access_level < 2:
		return {'error': 'You have no access to do that.'}

	_db = db_api.database_driver()
	con, cur = _db._get_connection()

	record = await _db.delete_record(record_id)
	if record: return {'error': True, 'message': 'The record couldn\'t be deleted.'}
	return {'error': False}

@router.put('/record/{record_id}')
async def update_record(request: Request, record_id: int, record_data: dict, Authorization: str = Cookie(None)):
	user = auth_check(Authorization)
	if not user: return RedirectResponse(url='/')
	elif user.access_level < 2:
		return {'error': 'You have no access to do that.'}

	_db = db_api.database_driver()
	con, cur = _db._get_connection()

	record = await _db.update_record(record_id, record_data)
	return {'error': False}

@router.post('/auth')
async def user_auth(response: Response, request_payload: UserAuth):
	user = await auth_user(request_payload)
	if user['error']:
		return JSONResponse(user, status_code=user['error_code'])

	response.set_cookie(key='Authorization', value=user['response']['access_token'], httponly=True)
	return user['response']

@router.post('/register')
async def user_register(response: Response, request_payload: UserCreate):
	if request_payload.access_hash != hashlib.md5(f'{request_payload.username}|{request_payload.password}|{len(request_payload.username)+len(request_payload.password)}_69'.encode('utf-8')).hexdigest():
		return {'error': True, 'message': 'You have no access to do that.'}
	user = await create_user(request_payload)
	if user['error']:
		return JSONResponse(user, status_code=user['error_code'])

	response.set_cookie(key='Authorization', value=user['response']['access_token'], httponly=True)
	return user['response']
