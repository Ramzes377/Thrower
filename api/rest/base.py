from fastapi import FastAPI
from starlette.responses import RedirectResponse
from api.rest.v1 import router

app = FastAPI()
app.include_router(router)


@app.get('/')
def home():
    return RedirectResponse("docs")


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('api.rest.base:app', host='localhost', port=8000, reload=True)
