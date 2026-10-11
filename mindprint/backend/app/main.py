import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, patients, chat, journal, exercises, analytics, waitlist
from app.core.config import settings
from app.services.ai.base import ProviderError
from app.seed import seed

@asynccontextmanager
async def lifespan(app):
    await seed()
    yield

app=FastAPI(title='MINDPRINT AI',version='0.1.0',lifespan=lifespan)
origins=settings().allowed_origins.split(',')
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=['GET','POST','PUT','DELETE'],allow_headers=['Content-Type'])

@app.middleware('http')
async def guards(request:Request,call_next):
    if request.method in {'POST','PUT','DELETE','PATCH'}:
        origin=request.headers.get('origin')
        if (origin and origin not in origins) or request.headers.get('sec-fetch-site')=='cross-site':
            return JSONResponse(status_code=403,content={'detail':'Недопустимый источник запроса'})
        try:
            if int(request.headers.get('content-length','0')) > 100000:
                return JSONResponse(status_code=413,content={'detail':'Запрос слишком большой'})
        except ValueError:
            return JSONResponse(status_code=400,content={'detail':'Некорректный запрос'})
    try:
        response=await call_next(request)
    except Exception as exc:
        logging.getLogger('mindprint').error('Request failed: %s',type(exc).__name__)
        return JSONResponse(status_code=500,content={'detail':'Не удалось выполнить действие. Попробуйте ещё раз.'})
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Cache-Control']='no-store'
    return response

@app.exception_handler(ProviderError)
async def provider_error(request,exc):
    return JSONResponse(status_code=503,content={'detail':str(exc)})

@app.exception_handler(Exception)
async def unexpected(request,exc):
    logging.getLogger('mindprint').error('Request failed: %s',type(exc).__name__)
    return JSONResponse(status_code=500,content={'detail':'Не удалось выполнить действие. Попробуйте ещё раз.'})

@app.get('/api/health')
async def health():
    return {'status':'ok'}

for module in [auth,patients,chat,journal,exercises,analytics,waitlist]:
    app.include_router(module.router,prefix='/api')
