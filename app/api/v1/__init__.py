from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.lists import router as lists_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.friends import router as friends_router
from app.api.v1.endpoints.sessions import router as sessions_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(lists_router)
router.include_router(users_router)
router.include_router(friends_router)
router.include_router(sessions_router)