from fastapi import FastAPI
from starlette.responses import RedirectResponse
from api.rest.v1 import router


scheme = 'http'
domain = "127.0.0.1"
port = 8000
api_version = "v1"

base_url = f'{scheme}://{domain}:{port}/{api_version}/'

app = FastAPI()
app.include_router(router)


@app.get('/')
def home():
    return RedirectResponse("docs")


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('api.rest.base:app', host=domain, port=port, reload=True)
