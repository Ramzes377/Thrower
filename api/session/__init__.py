from fastapi import Depends, APIRouter, status

from .services import SrvSession
from api import tables
from api.schemas import (Session, User, Prescence, Activity, Leadership,
                         EndSession)
from api.specification import SessionID, MessageID, LeaderID, SessionMember

router = APIRouter(prefix='/session', tags=['session'])


@router.post('', response_model=Session, status_code=status.HTTP_201_CREATED)
async def session(sess: Session, service: SrvSession = Depends()):
    return await service.post(sess)


@router.get('', response_model=list[Session])
async def all_sessions(
    timestamps: SrvSession.filter_by_timeperiod = Depends(),
    service: SrvSession = Depends()
):
    return await service.all(timestamps)


@router.get('/unclosed', response_model=list[Session])
async def get_unclosed_sessions(service: SrvSession = Depends()):
    return await service.unclosed()


@router.get('/unclosed/{leader_id}', response_model=Session | None)
async def get_user_unclosed_session(
    leader_id: LeaderID = Depends(),
    service: SrvSession = Depends()
):
    return await service.user_unclosed(leader_id)


@router.get('/{session_id}', response_model=Session)
async def session(
    session_id: SessionID = Depends(),
    service: SrvSession = Depends()
):
    return await service.get(session_id)


@router.patch('/{session_id}', response_model=Session)
async def session(
    session_id: SessionID = Depends(),
    sess_data: Session | EndSession | dict = None,
    service: SrvSession = Depends()
):
    return await service.patch(session_id, sess_data)


@router.get('/{session_id}/members', response_model=list[User])
async def session_users(
    session_id: SessionID = Depends(),
    service: SrvSession = Depends()
):
    sess: tables.Session = await service.get(session_id)
    return sess.members


@router.post('/{session_id}/members/{user_id}', response_model=User,
             status_code=status.HTTP_201_CREATED)
async def session_add_member(
    session_id: SessionID = Depends(),
    user_id: SessionMember = Depends(),
    service: SrvSession = Depends()
):
    return await service.add_member(session_id, user_id)


@router.get('/by_msg/{message_id}', response_model=Session)
async def session(
    message_id: MessageID = Depends(),
    service: SrvSession = Depends()
):
    return await service.get(message_id)


@router.get('/{message_id}/activities', response_model=list[Activity])
async def session_activities(
    message_id: MessageID = Depends(),
    service: SrvSession = Depends()
):
    sess: tables.Session = await service.get(message_id)
    return sess.activities


@router.get('/{message_id}/leadership', response_model=list[Leadership])
async def session_leadership(
    message_id: MessageID = Depends(),
    service: SrvSession = Depends()
):
    sess: tables.Session = await service.get(message_id)
    return sess.leadership


@router.get('/{message_id}/prescence', response_model=list[Prescence])
async def session_prescence(
    message_id: MessageID = Depends(),
    service: SrvSession = Depends()
):
    sess: tables.Session = await service.get(message_id)
    return sess.prescence
