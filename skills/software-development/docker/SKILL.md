---
name: docker
description: "Docker container management — build, run, debug, and manage containers in sandboxed environments."
version: 1.0.0
author: Hermes Agent (adapted from OpenHands docker)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [docker, containers, containerization, devops, deployment]
    related_skills: [ssh, kubernetes, systematic-debugging]
---

# Docker Operations

Complete Docker workflow — building images, running containers, debugging, and cleanup.

## The Iron Law

```
CONTAINERS ARE EPHEMERAL. EXTERNALIZE STATE. NEVER STORE DATA IN A CONTAINER.
```

## Setup

### Install Docker
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y docker.io
sudo usermod -aG docker $USER
# Log out and back in for group changes

# Or use Docker's official script
curl -fsSL https://get.docker.com | sh
```

### Verify installation
```bash
docker --version
docker run hello-world
```

## Dockerfile Best Practices

### Basic template
```dockerfile
# Multi-stage build for smaller images
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim

# Copy only installed packages
COPY --from=builder /install /usr/local

WORKDIR /app
COPY . .

# Non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Key rules:
- Use specific tags, not `latest`
- Multi-stage builds for smaller images
- `.dockerignore` to exclude unnecessary files
- Run as non-root user
- One process per container
- Layer caching: put rarely-changing layers first

### .dockerignore
```
.git
__pycache__
*.pyc
.env
node_modules
.gitignore
*.md
```

## Building Images

```bash
# Build with tag
docker build -t myapp:latest .

# Build with specific Dockerfile
docker build -f Dockerfile.dev -t myapp:dev .

# Build with build args
docker build --build-arg VERSION=1.0.0 -t myapp:1.0.0 .

# Build with no cache (force fresh)
docker build --no-cache -t myapp:latest .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 -t myapp:latest .
```

## Running Containers

```bash
# Basic run
docker run myapp:latest

# Run with port mapping
docker run -p 8000:8000 myapp:latest

# Run with environment variables
docker run -e DATABASE_URL=postgres://db -e DEBUG=1 myapp:latest

# Run with env file
docker run --env-file .env myapp:latest

# Run with volume mount
docker run -v $(pwd)/data:/app/data myapp:latest

# Run in background (detached)
docker run -d --name myapp -p 8000:8000 myapp:latest

# Run interactively with shell
docker run -it myapp:latest /bin/sh

# Run with auto-cleanup (removes container on stop)
docker run --rm -it myapp:latest

# Run with resource limits
docker run --memory=512m --cpus=1.0 myapp:latest

# Run with network access to host
docker run --network=host myapp:latest
```

## Managing Containers

### List containers
```bash
docker ps           # Running only
docker ps -a        # All (including stopped)
```

### Stop/start/restart
```bash
docker stop myapp
docker start myapp
docker restart myapp
```

### Remove containers
```bash
docker rm myapp           # Remove stopped container
docker rm -f myapp        # Force remove (running too)
docker container prune    # Remove ALL stopped containers
```

### View logs
```bash
docker logs myapp
docker logs -f myapp      # Follow (tail -f)
docker logs --tail 100 myapp  # Last 100 lines
docker logs --since 1h myapp  # Last hour
```

### Execute commands in running container
```bash
docker exec -it myapp /bin/sh
docker exec -it myapp python manage.py migrate
docker exec -it myapp cat /var/log/app.log
```

### Copy files to/from container
```bash
docker cp myapp:/app/log.txt ./local_log.txt
docker cp ./local_file.txt myapp:/app/data/
```

### Inspect container
```bash
docker inspect myapp
docker stats myapp       # Resource usage (CPU, memory, network)
docker top myapp         # Running processes
```

## Docker Networks

```bash
# Create a network
docker network create mynetwork

# Run containers on the same network (can reference by name)
docker run -d --name db --network mynetwork postgres:15
docker run -d --name app --network mynetwork myapp
# App can connect to postgres using hostname "db"

# List networks
docker network ls

# Inspect network
docker network inspect mynetwork
```

## Docker Volumes

```bash
# Create named volume
docker volume create mydata

# Run with named volume
docker run -v mydata:/app/data myapp

# Run with bind mount (host path)
docker run -v /host/path:/container/path myapp

# List volumes
docker volume ls

# Inspect volume
docker volume inspect mydata

# Remove unused volumes
docker volume prune
```

## Docker Compose

### Basic docker-compose.yml
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
    volumes:
      - ./src:/app/src           # Hot reload
      - app_data:/app/data       # Named volume
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  app_data:
  db_data:
```

### Compose commands
```bash
docker compose up -d           # Start in background
docker compose up --build      # Rebuild and start
docker compose down            # Stop and remove
docker compose down -v         # Also remove volumes
docker compose logs -f app     # Follow logs
docker compose exec app sh     # Shell into container
docker compose ps              # List services
```

## Debugging

### Container won't start
```bash
# Check logs even if exited
docker logs <container_id>

# Run interactively to see error
docker run -it --rm myapp:latest /bin/sh
```

### Container exits immediately
```bash
# Check exit code
docker inspect <container_id> --format='{{.State.ExitCode}}'

# Keep container alive for debugging
docker run -it --entrypoint /bin/sh myapp:latest
```

### Network issues
```bash
# Test connectivity between containers
docker exec app ping db
docker exec app curl http://db:5432

# Check exposed ports
docker port myapp
```

### Resource issues
```bash
# Check resource usage
docker stats

# Check disk usage
docker system df

# Full system info
docker system info
```

## Cleanup

```bash
# Remove all stopped containers
docker container prune

# Remove all unused images
docker image prune -a

# Remove all unused volumes
docker volume prune

# Remove everything (nuclear option)
docker system prune -a --volumes
```

## Common Patterns

### Development with hot reload
```bash
docker run -v $(pwd):/app -p 8000:8000 myapp:dev
```

### Database for development
```bash
docker run -d --name dev-db \
  -e POSTGRES_PASSWORD=devpass \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  postgres:15
```

### One-off command in a container
```bash
docker run --rm -v $(pwd):/app python:3.12-slim python /app/script.py
```
