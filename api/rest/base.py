from functools import partial

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from starlette.responses import RedirectResponse
from httpx import AsyncClient

from api.rest.v1 import router

base = "http://127.0.0.1:8000"
api_ver = "v1"
base_url = f'{base}/{api_ver}'

app = FastAPI()
app.include_router(router)

AsyncHttpClient = partial(AsyncClient, app=app, base_url=base_url)


async def request(url: str, method: str = 'get', data: dict | None = None):
    async with AsyncHttpClient() as client:
        if method in ('get', 'delete'):
            response = await client.request(method, url)
        else:
            _method = getattr(client, method)
            response = await _method(url, json=jsonable_encoder(data))
        return response.json()


@app.get('/')
def home():
    return RedirectResponse("docs")


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('api.rest.base:app', host='127.0.0.1', port=8000, reload=True)
