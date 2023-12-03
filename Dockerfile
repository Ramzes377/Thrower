FROM python:3.11.6-alpine

# Set work directory
WORKDIR /usr/src/bot

# Copy only necessary files
COPY . .

# Install pre-dependencies and dependencies
RUN apk add --no-cache build-base \
&& pip install --upgrade pip \
&& pip install poetry \
&& poetry config virtualenvs.create false \
&& poetry install --without dev --no-root \
&& pip uninstall -y poetry \
&& rm -rf /root/.cache/pypoetry

WORKDIR /usr/src/bot

# Set the entrypoint
ENTRYPOINT ["python", "-u", "__main__.py"]