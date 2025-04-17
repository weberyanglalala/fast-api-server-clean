# Build stage
FROM python:3.12-slim

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Disable Poetry virtualenvs so dependencies are installed globally
ENV POETRY_VIRTUALENVS_CREATE=false

# Copy pyproject.toml and poetry.lock first for better cache
COPY pyproject.toml poetry.lock* ./

# Install dependencies using Poetry
RUN poetry install --no-root --no-interaction --no-ansi

# Copy the project files
COPY src/ src/

# Expose the port FastAPI runs on
EXPOSE 8000

# Run the FastAPI application
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]