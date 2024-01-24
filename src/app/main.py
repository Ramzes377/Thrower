import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, responses

from src.app.service import Service
from src.app.routers import router
from src.config import Config


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """ Init deferred task event loop when running web server manually. """
    loop = asyncio.get_event_loop()
    asyncio.create_task(Service.deferrer.start(loop=loop))  # noqa
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)


@app.get('/')
def home():
    return responses.RedirectResponse("docs")


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app='main:app',
        host=Config.api_host,
        port=Config.api_port,
        reload=True,
    )
