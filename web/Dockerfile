# syntax=docker/dockerfile:1
FROM node:22-alpine AS client
WORKDIR /build
COPY client/package.json client/package-lock.json ./
RUN npm ci
COPY client/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    F95WEB_HOST=0.0.0.0 \
    F95CHECKER_DATA_DIR=/data

COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

COPY server/ server/
COPY --from=client /build/dist client/dist

VOLUME ["/data"]
EXPOSE 8642
CMD ["python", "server/run.py"]
