from fastapi import FastAPI
from fastapi.routing import APIRouter
from routes import routes
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://gitm8.local",
    "http://gitm8.local:8080",
    "http://localhost:5173",
    "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)
