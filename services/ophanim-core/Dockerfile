FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OPHANIM_ENVIRONMENT=development

WORKDIR /app

COPY pyproject.toml ./
COPY ophanim ./ophanim

RUN pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 ophanim \
    && mkdir -p /app/data \
    && chown -R ophanim:ophanim /app

USER ophanim

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)" || exit 1

CMD ["python", "-m", "uvicorn", "ophanim.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning"]
