# Clean Architecture Template

## Development

### Create a virtual environment

```
poetry install --no-root
```

### Activate the virtual environment

```
poetry shell
```

### Install all dependencies

- run `poetry install` to install all dependencies

### Using Docker with PostgreSQL

- Install Docker Desktop
- Run `docker compose up db` to start the PostgreSQL database
- Run `docker compose down` to stop all services

### modify the .env file

- Copy the `.env.example` file to `.env` and modify the values as needed

### How to run locally

```
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### How to run tests

```
poetry run pytest
```

## how to add migration by alembic

### Create a migration

```
alembic revision --autogenerate -m "migration_name"
```

### modify the database url in alembic.ini

- Change the `sqlalchemy.url` to your database URL
- For example, if you are using PostgreSQL, it should look like this:

```
sqlalchemy.url = postgresql://username:password@localhost:5432/db_name
```


### Apply the migration

#### run all services

```
docker compose up
```

#### exec the api container

```
docker compose exec api bash
```

```
alembic upgrade head
```
