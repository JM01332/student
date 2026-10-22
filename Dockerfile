# syntax=docker/dockerfile:1
# check=error=true

ARG PYTHON_IMAGE=python:3.15-trixie
ARG UV_VERSION=0.12.23

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM ${PYTHON_IMAGE} AS builder
COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /opt/app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/opt/app/.venv

# Abhängigkeiten getrennt vom Anwendungscode cachen.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-default-groups --no-editable

COPY README.md pyproject.toml ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --locked --no-default-groups --no-editable

FROM ${PYTHON_IMAGE} AS final
ARG APP_UID=10000
ARG APP_GID=10000

WORKDIR /opt/app
RUN groupadd --gid ${APP_GID} app \
    && useradd --uid ${APP_UID} --gid ${APP_GID} --no-create-home --shell /usr/sbin/nologin app \
    && mkdir /opt/app/log \
    && chown ${APP_UID}:${APP_GID} /opt/app/log

COPY --from=builder /opt/app/.venv /opt/app/.venv
ENV PATH="/opt/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER ${APP_UID}:${APP_GID}
EXPOSE 8000
STOPSIGNAL SIGINT
ENTRYPOINT ["python", "-m", "student"]
