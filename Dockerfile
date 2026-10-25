FROM python:3.10-slim

# parec/pactl talk to the host's PulseAudio/PipeWire socket mounted by docker-compose.
RUN apt-get update && apt-get install -y --no-install-recommends pulseaudio-utils ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu ".[server]"

ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "meetai.server.main:app", "--host", "0.0.0.0", "--port", "8000"]
