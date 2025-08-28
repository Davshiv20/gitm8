FROM python:3.11-slim
WORKDIR /app
# If using Poetry:
COPY backend/pyproject.toml backend/poetry.lock ./ 
RUN pip install --no-cache-dir poetry && poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --only main
COPY backend /app
ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  