# syntax=docker/dockerfile:1
FROM node:22-slim AS client
WORKDIR /build
RUN npm install -g pnpm@12.14.0
COPY client/package.json client/pnpm-lock.yaml client/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY client/ ./
RUN pnpm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    F95CHECKER_DATA_DIR=/data \
    F95WEB_HOST=0.0.0.0 \
    F95WEB_PORT=8642 \
    F95BROWSER_LOGIN=0

COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

COPY server/ server/
# The server itself serves the built SPA from client/dist (app/main.py spa_fallback).
COPY --from=client /build/dist client/dist

VOLUME ["/data"]
EXPOSE 8642
CMD ["python", "server/run.py"]
