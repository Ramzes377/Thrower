from fastapi import APIRouter

from src.app.routers.activity import router as activity_router
from src.app.routers.activity_info import router as activity_info_router
from src.app.routers.emoji import router as emoji_router
from src.app.routers.leadership import router as leadership_router
from src.app.routers.music import router as music_router
from src.app.routers.prescence import router as prescence_router
from src.app.routers.role import router as role_router
from src.app.routers.session import router as sess_router
from src.app.routers.user import router as user_router
from src.app.routers.sent_message import router as sent_message_router
from src.app.routers.guild import router as guild_router

router = APIRouter(prefix='')
router.include_router(sess_router)
router.include_router(user_router)
router.include_router(activity_info_router)
router.include_router(activity_router)
router.include_router(prescence_router)
router.include_router(leadership_router)
router.include_router(role_router)
router.include_router(emoji_router)
router.include_router(music_router)
router.include_router(sent_message_router)
router.include_router(guild_router)
