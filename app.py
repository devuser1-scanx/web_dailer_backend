# app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import APP_NAME

from routes.health import router as health_router
from routes.patients import router as patients_router
from routes.calls import router as calls_router
from routes.websocket import router as websocket_router
from routes.notifications import router as notifications_router
from routes.dev import router as dev_router
from routes.voice import router as voice_router

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this once frontend URL is known
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(patients_router)
app.include_router(calls_router)
app.include_router(websocket_router)
app.include_router(notifications_router)
app.include_router(dev_router)
app.include_router(voice_router)


@app.get("/")
def root():
    return {
        "service": APP_NAME,
        "status": "running",
    }