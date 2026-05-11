# app/main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from app.api.v1 import router as v1_router

# Импорты WebSocket обработчиков
from app.api.v1.endpoints.sessions_ws import sessions_websocket
from app.api.v1.endpoints.global_ws import global_websocket
from app.events.registry import init_events

init_events()

app = FastAPI(
    title="Decido API",
    version="1.0.0",
    description="API for collaborative decision making"
)

# Добавляем пагинацию
add_pagination(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем v1 API
app.include_router(v1_router)

# WebSocket эндпоинты
@app.websocket("/api/v1/sessions/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: int, token: str = None):
    await sessions_websocket(websocket, session_id, token)


@app.websocket("/api/v1/global")
async def global_ws_endpoint(websocket: WebSocket, token: str = None):
    await global_websocket(websocket, token)


@app.get("/")
async def root():
    return {"message": "Hello from Decido API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}