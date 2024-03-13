from fastapi import FastAPI, Request, Cookie, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from urllib.parse import urlparse

import json, os

from .api.routers import router as api_router
from .api.auth import auth_check

####################################################
#os.chdir('./my_fastapi')
os.makedirs('./files', exist_ok=True)

app = FastAPI(docs_url=None, redoc_url=None, tags=[])
app.include_router(api_router)

templates = Jinja2Templates(directory="templates")

@app.get('/')
async def root(request: Request, Authorization: str = Cookie(None)):
	user = auth_check(Authorization)
	if not user: return RedirectResponse(url='/login')
	elif user.access_level == 0:
		raise HTTPException(status_code=404, detail="Item not found")
	elif user.access_level > 0:
		return RedirectResponse(url='/records/search')

@app.get('/login')
async def route_login(request: Request, Authorization: str = Cookie(None)):
	user = auth_check(Authorization)
	if user: return RedirectResponse(url='/')

	return templates.TemplateResponse("login.html", {"request": request})

@app.get('/logout')
async def route_logout(request: Request):
	response = templates.TemplateResponse("login.html", {"request": request})
	response.delete_cookie("Authorization")
	return response

@app.get('/records/search')
async def route_orders_search(request: Request, Authorization: str = Cookie(None)):
	user = auth_check(Authorization)

	if not user:
		return RedirectResponse(url='/login')
	elif user.access_level == 0:
		raise HTTPException(status_code=404, detail="Item not found")

	return templates.TemplateResponse("records_search.html", {"request": request})

@app.get('/records/add')
async def route_orders_add(request: Request, Authorization: str = Cookie(None)):
	user = auth_check(Authorization)

	if not user:
		return RedirectResponse(url='/login')
	elif user.access_level == 0:
		raise HTTPException(status_code=404, detail="Item not found")
	elif user.access_level == 1:
		return RedirectResponse(url='/records/search')

	return templates.TemplateResponse("records_add.html", {"request": request})

@app.get('/records/edit')
async def route_orders_add(request: Request, Authorization: str = Cookie(None)):
	user = auth_check(Authorization)

	if not user:
		return RedirectResponse(url='/login')
	elif user.access_level == 0:
		raise HTTPException(status_code=404, detail="Item not found")
	elif user.access_level == 1:
		return RedirectResponse(url='/records/search')

	return templates.TemplateResponse("records_edit.html", {"request": request})

@app.get('/files/{path:path}')
async def route_get_file(path: str, Authorization: str = Cookie(None)):
	user = auth_check(Authorization)

	if not user:
		return RedirectResponse(url='/login')
	elif user.access_level == 0:
		raise HTTPException(status_code=404, detail="Item not found")

	path_ = urlparse(path)
	path_ = path_.path[:-1] if path_.path[-1] == '/' else path_.path
	path = f'files/{path_}' if f'files/{path_}' == '/' else f'files/{path_}'
	if os.path.exists(path): return FileResponse(path=path, filename=path_[len(path_.split('_')[0])-1:])
	
	raise HTTPException(status_code=404, detail="File not found")


@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: HTTPException):
	return templates.TemplateResponse('404.html', {'request': request}, status_code=404)

@app.exception_handler(500)
async def internal_error_exception_handler(request: Request, exc: HTTPException):
	return templates.TemplateResponse('500.html', {'request': request}, status_code=500)

if __name__ == '__main__':
	uvicorn.run()