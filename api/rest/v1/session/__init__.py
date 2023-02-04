from fastapi import Depends, APIRouter, status

from .specifications import LeaderID
from .services import SrvSession
from .. import tables
from ..schemas import Session, Member, Prescence, Activity, Leadership, EndSession
from ..specifications import SessionID, MessageID
from ..user.specifications import UserID

router = APIRouter(prefix='/session', tags=['session'])


@router.post('/', response_model=Session, status_code=status.HTTP_201_CREATED)
def session(sess: Session, service: SrvSession = Depends()):
    return service.post(sess)


@router.get('/', response_model=list[Session])
def all_sessions(timestamps: SrvSession.filter_by_timeperiod = Depends(), service: SrvSession = Depends()):
    return service.all(timestamps)


@router.get('/unclosed/', response_model=list[Session])
def get_unclosed_sessions(service: SrvSession = Depends()):
    return service.unclosed()


@router.get('/unclosed/{leader_id}', response_model=Session | None)
def get_user_unclosed_session(leader_id: LeaderID = Depends(), service: SrvSession = Depends()):
    return service.user_unclosed(leader_id)


@router.get('/{session_id}', response_model=Session)
def session(session_id: SessionID = Depends(), service: SrvSession = Depends()):
    return service.get(session_id)


@router.patch('/{session_id}', response_model=Session)
def session(session_id: SessionID = Depends(),
            sess_data: Session | EndSession | dict = None,
            service: SrvSession = Depends()):
    return service.patch(session_id, sess_data)


@router.get('/{session_id}/members', response_model=list[Member])
def session_users(session_id: SessionID = Depends(), service: SrvSession = Depends()):
    sess: tables.Session = service.get(session_id)
    return sess.members


@router.post('/{session_id}/members/{user_id}', response_model=Member, status_code=status.HTTP_201_CREATED)
def session_add_member(session_id: SessionID = Depends(),
                       user_id: UserID = Depends(),
                       service: SrvSession = Depends()):
    return service.add_member(session_id, user_id)


@router.get('/by_msg/{message_id}', response_model=Session)
def session(message_id: MessageID = Depends(), service: SrvSession = Depends()):
    return service.get(message_id)


@router.get('/{message_id}/activities', response_model=list[Activity])
def session_activities(message_id: MessageID = Depends(), service: SrvSession = Depends()):
    sess: tables.Session = service.get(message_id)
    return sess.activities


@router.get('/{message_id}/leadership', response_model=list[Leadership])
def session_leadership(message_id: MessageID = Depends(), service: SrvSession = Depends()):
    sess: tables.Session = service.get(message_id)
    return sess.leadership


@router.get('/{message_id}/prescence', response_model=list[Prescence])
def session_prescence(message_id: MessageID = Depends(), service: SrvSession = Depends()):
    sess: tables.Session = service.get(message_id)
    return sess.prescence
