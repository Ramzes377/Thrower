from fastapi import APIRouter

from api.rest.v1.session import router as sess_router
from api.rest.v1.user import router as user_router
from api.rest.v1.activity import router as activity_router
from api.rest.v1.prescence import router as prescence_router
from api.rest.v1.leadership import router as leadership_router
from api.rest.v1.role import router as role_router
from api.rest.v1.emoji import router as emoji_router
from api.rest.v1.music import router as music_router


router = APIRouter(prefix='/v1')
router.include_router(sess_router)
router.include_router(user_router)
router.include_router(activity_router)
router.include_router(prescence_router)
router.include_router(leadership_router)
router.include_router(role_router)
router.include_router(emoji_router)
router.include_router(music_router)