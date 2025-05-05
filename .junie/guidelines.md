# FastAPI Clean Architecture Project Guidelines

This document provides essential information for developers working on this FastAPI Clean Architecture project.

## Build/Configuration Instructions

### Local Development Setup

1. **Clone the repository and install dependencies**:
   ```bash
   # Install Poetry if not already installed
   pip install poetry
   
   # Install dependencies
   poetry install
   ```

2. **Environment Variables**:
   - Copy `.env.example` to `.env` and fill in the required values:
   ```bash
   cp .env.example .env
   ```
   - Required environment variables include:
     - `DATABASE_URL`: PostgreSQL connection string
     - `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT_URL`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL`: Cloudflare R2 storage configuration
     - `SECRET_KEY`: For JWT token generation
     - `ACCESS_TOKEN_EXPIRE_DAYS`: JWT token expiration
     - `OPENAI_API_KEY`: For OpenAI integration

3. **Run Database Migrations**:
   ```bash
   poetry run alembic upgrade head
   ```

4. **Start the Development Server**:
   ```bash
   poetry run uvicorn src.main:app --reload
   ```

### Docker Setup

1. **Build and Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Access the API**:
   - The API will be available at `http://localhost:8000`
   - Swagger UI documentation at `http://localhost:8000/docs`

## Testing Information

### Running Tests

1. **Run All Tests**:
   ```bash
   poetry run pytest
   ```

2. **Run Specific Test Files**:
   ```bash
   poetry run pytest tests/test_string_utils.py
   ```

3. **Run Tests with Verbose Output**:
   ```bash
   poetry run pytest -v
   ```

4. **Run Tests with Coverage Report**:
   ```bash
   poetry run pytest --cov=src
   ```

### Test Structure

- **Unit Tests**: Located in the `tests` directory, test individual components
- **End-to-End Tests**: Located in the `tests/e2e` directory, test API endpoints

### Writing New Tests

1. **Unit Tests**:
   - Create a new file in the `tests` directory with the naming convention `test_*.py`
   - Use pytest fixtures from `conftest.py` for database and authentication setup
   - Example:
   ```python
   import pytest
   from src.utils.string_utils import slugify

   def test_slugify_basic():
       assert slugify("Hello World") == "hello-world"
   ```

2. **End-to-End Tests**:
   - Create a new file in the `tests/e2e` directory
   - Use the `client` and `auth_headers` fixtures for API testing
   - Example:
   ```python
   def test_endpoint(client, auth_headers):
       response = client.get("/endpoint", headers=auth_headers)
       assert response.status_code == 200
   ```

## Project Structure

The project follows a clean architecture pattern:

- **Controllers**: Handle HTTP requests and responses (`src/*/controller.py`)
- **Services**: Contain business logic (`src/*/service.py`)
- **Models**: Define data structures (`src/*/models.py`)
- **Entities**: Define database models (`src/entities/*.py`)
- **Utils**: Utility functions (`src/utils/*.py`)

## Code Style and Development Guidelines

1. **Code Formatting**:
   - Use Black for code formatting:
   ```bash
   poetry run black src tests
   ```

2. **Linting**:
   - Use Ruff for linting:
   ```bash
   poetry run ruff check src tests
   ```

3. **Type Checking**:
   - Use type hints throughout the codebase
   - Function signatures should include parameter and return types

4. **API Development**:
   - Follow RESTful principles
   - Use Pydantic models for request/response validation
   - Document API endpoints with docstrings and OpenAPI annotations

5. **Database Migrations**:
   - Create new migrations with Alembic:
   ```bash
   poetry run alembic revision --autogenerate -m "description"
   ```
   - Apply migrations:
   ```bash
   poetry run alembic upgrade head
   ```

6. **Error Handling**:
   - Use custom exceptions defined in `src/exceptions.py`
   - Let the exception handlers middleware handle converting exceptions to HTTP responses

## Debugging

1. **Logging**:
   - The application uses Python's logging module
   - Log levels can be configured in `src/log_config.py`
   - Logs are output to the console by default

2. **Interactive Debugging**:
   - Use the FastAPI debug mode with `--reload` flag
   - Set breakpoints in your IDE or use Python's `breakpoint()` function