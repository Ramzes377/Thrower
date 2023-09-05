import fastapi
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient

from bot.api.rest.v1 import router

base = "http://127.0.0.1:8000"
api_ver = "v1"
base_url = f'{base}/{api_ver}'

app = fastapi.FastAPI()
app.include_router(router)


async def request(
        url: str,
        method: str = 'get',
        data: dict | None = None,
        params: dict | None = None
) -> dict:
    async with AsyncClient(app=app, base_url=base_url) as client:

        if method in ('get', 'delete'):
            response = await client.request(method, url, params=params)
        else:
            data = jsonable_encoder(data)
            response = await client.request(method, url, params=params,
                                            json=data)

    return response.json()


@app.get('/')
def home():
    return fastapi.responses.RedirectResponse("docs")


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app='bot.api.rest.base:app',
        host='127.0.0.1',
        port=8000,
        reload=True
    )
