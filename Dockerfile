ARG PYTHON_VERSION="3.11.6"
FROM python:${PYTHON_VERSION}-slim-bookworm

WORKDIR /root

# Install python requirements
COPY Pipfile /tmp/
RUN --mount=type=secret,id=codeartifact-token,dst=/codeartifact-token export CODEARTIFACT_AUTH_TOKEN=$(cat /codeartifact-token) && \
    pip install pipenv==2022.8.15 && \
    cd /tmp && \
    pipenv lock && \
    pipenv requirements > /tmp/requirements.txt && \
    pip install -r /tmp/requirements.txt && \
    pipenv --clear && \
    pip cache purge

COPY ./src/ /root/auto-decisions/src

ENV PYTHONPATH=/root/auto-decisions
