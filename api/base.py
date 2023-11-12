import asyncio

import fastapi

from api.service import Service
from api import router
from config import Config

app = fastapi.FastAPI()
app.include_router(router)


@app.get('/')
def home():
    return fastapi.responses.RedirectResponse("docs")


@app.on_event("startup")
async def startup_event():
    """ Init deferred task event loop when running web server manually. """

    asyncio.create_task(Service.deferrer.start())


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app='api.base:app',
        host=Config.api_host,
        port=Config.api_port,
        reload=True,
    )
