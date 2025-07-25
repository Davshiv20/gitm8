from fastapi import FastAPI
from fastapi.routing import APIRouter
from routes import routes

app = FastAPI()

app.include_router(routes.router)
