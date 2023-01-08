from fastapi import Depends, APIRouter

from ..schemas import Prescence
from .services import SrvPrescence

router = APIRouter(prefix='/prescence', tags=['prescence'])


@router.get('/{session_id}', response_model=list[Prescence])
def prescence(session_id: int, service: SrvPrescence = Depends()):
    return service.get(session_id)


@router.post('/', response_model=Prescence)
def prescence(prescencedata: Prescence, service: SrvPrescence = Depends()):
    return service.post(prescencedata)


@router.put('/', response_model=Prescence | None)
def prescence(prescencedata: dict, service: SrvPrescence = Depends()):
    return service.put(prescencedata)


@router.get('/by_msg/{message_id}', response_model=list[Prescence])
def prescence(message_id: int, service: SrvPrescence = Depends()):
    return service.get(message_id=message_id)
