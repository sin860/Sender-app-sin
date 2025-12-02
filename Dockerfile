
FROM python:3.10-slim


WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

CMD exec gunicorn --worker-class geventwebsocket.gunicorn.workers.GeveWorker -w 1 --bind 0.0.0.0:${PORT} app:app
