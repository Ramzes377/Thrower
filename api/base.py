import fastapi


from api import router
from config import Config

app = fastapi.FastAPI()
app.include_router(router)


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
