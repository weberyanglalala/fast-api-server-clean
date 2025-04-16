# Clean Architecture Template

What's included in the template?

- Domain layer with sample entities.
- Application layer with abstractions for:
  - Example use cases
  - Cross-cutting concerns (logging, validation)
- Infrastructure layer with:
  - Authentication
  - SQLAlchemy, PostgreSQL (you can change to SQLite for development in database/core.py)
  - Rate limiting on registration
- Testing projects
  - Pytest unit tests
  - Pytest integration tests (e2e tests)

I'm open to hearing your feedback about the template and what you'd like to see in future iterations. DM me on LinkedIn or email me.

--

## Create a virtual environment

- Run `python -m venv .venv` to create a virtual environment.
- Run `source .venv/bin/activate` to activate the virtual environment on Mac/Linux.

## Install all dependencies

- Run `pip install -r requirements-dev.txt`

## How to run app. Using Docker with PostgreSQL

- Install Docker Desktop
- Run `docker compose up --build`
- Run `docker compose down` to stop all services

## How to run locally

- run `uvicorn src.main:app --reload`

## How to run tests

- Run `pytest` to run all tests

Cheers!
