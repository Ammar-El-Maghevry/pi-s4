FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Slow/flaky networks (e.g. CI or constrained dev environments) can trip pip's
# default 15s read timeout on large wheels (opencv, onnxruntime, av); raise it
# and retry instead of failing the whole build on a single stalled chunk.
ENV PIP_DEFAULT_TIMEOUT=100
RUN pip install --no-cache-dir --retries 10 -r requirements.txt

COPY . .

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
