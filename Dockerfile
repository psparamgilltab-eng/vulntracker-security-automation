
FROM python:3.11-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATABASE_URL=sqlite:////data/vulntracker.db

WORKDIR /app

# Install OS security updates and remove package lists.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# Copy pinned dependencies before installing them.
COPY requirements.txt /tmp/requirements.txt

# Install application dependencies and final pinned packaging tools.
RUN python -m pip install --no-cache-dir --upgrade \
        "pip==26.2.0" \
        "wheel==0.46.2" \
        "jaraco.context==6.1.0" \
    && python -m pip install --no-cache-dir -r /tmp/requirements.txt \
    && groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid 10001 --no-create-home appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /data

COPY --chown=appuser:appuser app/ /app/

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
