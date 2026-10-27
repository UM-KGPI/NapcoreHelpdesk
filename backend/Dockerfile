FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# -m creates /home/napcore: the model download keeps its cache under $HOME.
RUN groupadd -r napcore && useradd -r -m -g napcore napcore

WORKDIR /app/backend


RUN apt-get update \
    && apt-get install -y --no-install-recommends curl git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install --no-cache-dir gunicorn==23.0.0

COPY . /app/backend

# /app/repos holds the checkouts of the indexed repositories and /models the embedding model (named
# volumes in production); creating them here gives a new volume the right owner on first use.
RUN mkdir -p /app/repos /models && chown -R napcore:napcore /app /models

USER napcore

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
