FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd -r napcore && useradd -r -g napcore napcore

WORKDIR /app/backend


RUN apt-get update \
    && apt-get install -y --no-install-recommends curl git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install --no-cache-dir gunicorn==23.0.0

COPY . /app/backend

# /app/repos holds the checkouts of the indexed repositories (a named volume in production);
# creating it here gives the volume the right owner on first use.
RUN mkdir -p /app/repos && chown -R napcore:napcore /app

USER napcore

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
