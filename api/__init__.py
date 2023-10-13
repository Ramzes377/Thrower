from fastapi import APIRouter

from api.service import crud_fabric

from api.activity import router as activity_router
from api.activity_info import router as activity_info_router
from api.emoji import router as emoji_router
from api.leadership import router as leadership_router
from api.music import router as music_router
from api.prescence import router as prescence_router
from api.role import router as role_router
from api.session import router as sess_router
from api.user import router as user_router
from api.sent_message import router as sent_message_router
from api.guild import router as guild_router

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
