import fastapi
from httpx import AsyncClient

from config import Config
from api import router

app = fastapi.FastAPI()
app.include_router(router)


async def request(
    url: str,
    method: str = 'get',
    data: dict | None = None,
    params: dict | None = None
) -> dict:
    async with AsyncClient(app=app, base_url=Config.BASE_URI) as client:
        if method in ('get', 'delete'):
            response = await client.request(method, url, params=params)
        else:
            data = fastapi.encoders.jsonable_encoder(data)  # noqa
            response = await client.request(
                method,
                url,
                params=params,
                json=data
            )

    return response.json()


@app.get('/')
def home():
    return fastapi.responses.RedirectResponse("docs")


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app='api.base:app',
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True,
    )
