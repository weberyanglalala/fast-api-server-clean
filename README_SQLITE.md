# Connecting to an External SQLite Database in Docker

This guide explains how to connect to an existing SQLite database from your Docker container using environment variables.

## Setup Instructions

### 1. Configure Environment Variables

Create or update your `.env` file with the following variables:

```
# SQLite Database Configuration
SQLITE_DB_PATH=/absolute/path/to/your/database.db
DATABASE_URL=sqlite:///${SQLITE_DB_PATH}

# Comment out PostgreSQL connection if you're switching to SQLite
# DATABASE_URL=postgresql://postgres:postgres@db:5432/cleanfastapi
```

Replace `/absolute/path/to/your/database.db` with the actual path to your SQLite database file on your host machine.

### 2. Docker Compose Configuration

The `docker-compose.yml` file has been updated to:
- Pass the `SQLITE_DB_PATH` environment variable to the container
- Mount the SQLite database file from your host machine to the container

The relevant sections in `docker-compose.yml` are:

```yaml
environment:
  - DATABASE_URL=${DATABASE_URL}
  - SQLITE_DB_PATH=${SQLITE_DB_PATH:-/app/data/default.db}
  # Other environment variables...

volumes:
  - ./src:/app/src
  # Mount the SQLite database file if using SQLite
  - ${SQLITE_DB_PATH:-./data/default.db}:${SQLITE_DB_PATH:-/app/data/default.db}
```

### 3. Running the Application

Start your application with Docker Compose:

```bash
docker-compose up --build
```

## Cross-Platform Considerations

When using SQLite with Docker across different computers, consider these approaches:

### Option 1: Use Absolute Paths (Current Implementation)

- Set `SQLITE_DB_PATH` to the absolute path on your host machine
- The Docker container will mount this path directly

This works well if each developer sets their own path in their local `.env` file.

### Option 2: Use a Relative Path Within the Project

For a more portable solution:

1. Place your SQLite database in a directory within your project (e.g., `./data/`)
2. Update your `.env` file:
   ```
   SQLITE_DB_PATH=/app/data/mydb.sqlite
   DATABASE_URL=sqlite:///${SQLITE_DB_PATH}
   ```
3. Update the volume mount in `docker-compose.yml`:
   ```yaml
   volumes:
     - ./src:/app/src
     - ./data:/app/data
   ```

This approach makes the setup more consistent across different computers.

## SQLite Connection String Format

The SQLite connection string format is:
- `sqlite:///path/to/database.db` (three slashes for absolute path)
- `sqlite:////absolute/path/from/root` (four slashes in Docker for absolute path from root)

## Read-Only Option

If you only need read access to the database, you can add `?mode=ro` to your connection string:
```
DATABASE_URL=sqlite:///${SQLITE_DB_PATH}?mode=ro
```

## Troubleshooting

1. **Permission Issues**: Ensure the Docker process has read/write permissions to the mounted SQLite database file.

2. **Path Not Found**: Double-check that the path in `SQLITE_DB_PATH` exists on your host machine.

3. **Connection Errors**: Verify that the SQLite connection string format is correct.