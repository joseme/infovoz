FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip && \
    unzip vosk-model-small-es-0.42.zip && \
    rm vosk-model-small-es-0.42.zip

FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libasound2-dev \
    mpg123 \
    ffmpeg \
    espeak \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=builder /vosk-model-small-es-0.42 /app/vosk-model-small-es-0.42

COPY . .

RUN mkdir -p /app/data && \
    adduser --disabled-password --gecos "" --uid 1000 appuser && \
    chown -R appuser:appuser /app

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

USER appuser

EXPOSE 8550

ENV FLET_WEB=true \
    VOSK_MODEL_PATH=/app/vosk-model-small-es-0.42 \
    USERS_FILE=/app/data/users.json

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "main.py"]
