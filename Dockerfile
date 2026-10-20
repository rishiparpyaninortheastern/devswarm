FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -c requirements.lock.txt ".[api]" && useradd --uid 10001 --create-home devswarm && mkdir /data && chown devswarm /data
USER devswarm
ENV DEVSWARM_DB=/data/devswarm.db
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
