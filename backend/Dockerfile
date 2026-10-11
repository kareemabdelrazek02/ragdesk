# --- build stage: install dependencies into a virtualenv ---
FROM python:3.12-slim AS build
WORKDIR /app
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

# --- runtime stage: copy only the virtualenv and source, run as non-root ---
FROM python:3.12-slim
WORKDIR /app
COPY --from=build /venv /venv
COPY app ./app
ENV PATH="/venv/bin:$PATH" PYTHONUNBUFFERED=1
RUN useradd --create-home appuser
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
