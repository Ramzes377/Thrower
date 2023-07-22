FROM python:3.11.4-slim-buster

# set work directory
WORKDIR usr/src/bot

# copy project
COPY /bot /usr/src/bot

# install pre-dependencies
RUN pip install --upgrade pip && \
    pip install poetry



# install dependencies, clear build files
RUN poetry install && poetry cache clear pypi --all

ENTRYPOINT ["poetry", "run", "python", "/usr/src/bot"]
