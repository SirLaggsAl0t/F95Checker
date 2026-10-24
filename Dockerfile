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
    CLIENT_PORT=5173 \
    F95BROWSER_LOGIN=0

COPY server/requirements.txt server/requirements.txt
# libstdc++6: the node binary copied below links it and the slim base may not ship it
RUN apt-get update \
    && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r server/requirements.txt

COPY server/ server/
# Built SPA plus the tooling needed to serve it on CLIENT_PORT; /api is proxied to the
# server on 127.0.0.1:8642 by client/vite.config.ts (preview inherits server.proxy).
COPY --from=client /usr/local/bin/node /usr/local/bin/node
COPY --from=client /build/node_modules client/node_modules
COPY --from=client /build/dist client/dist
COPY --from=client /build/package.json /build/vite.config.ts client/

VOLUME ["/data"]
EXPOSE ${CLIENT_PORT}
# Server binds 127.0.0.1 only (config default), so it is reachable from the client but
# never published. Server is PID 1 so uvicorn gets SIGTERM; the preview dies with it.
CMD ["sh", "-c", "node client/node_modules/vite/bin/vite.js preview client --host 0.0.0.0 --port \"$CLIENT_PORT\" --strictPort & exec python server/run.py"]
