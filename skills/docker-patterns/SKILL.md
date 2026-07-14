---
name: docker-patterns
description: Docker patterns, multi-stage builds, Docker Compose workflows, and container best practices for development and production.
origin: opencode
---

# Docker Patterns

## Multi-Stage Builds

```dockerfile
# Stage 1: Dependencies
FROM node:24-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

# Stage 2: Build
FROM node:24-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN corepack enable && pnpm build

# Stage 3: Production
FROM node:24-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
USER app
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

## Development Compose

```yaml
# docker-compose.dev.yml
services:
  app:
    build:
      context: .
      target: deps
    volumes:
      - .:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
    command: pnpm dev

  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: app
      POSTGRES_PASSWORD: ${DB_PASSWORD:-devpass}

volumes:
  pgdata:
```

## Production Compose

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    restart: unless-stopped

volumes:
  pgdata:
```

## Security

- Never run as root inside container (use `USER` directive)
- Use read-only root filesystem when possible
- Pin base image versions (no `latest`)
- Use `.dockerignore` to exclude secrets and node_modules
- Scan images with `docker scout`
- Set resource limits (`--memory`, `--cpus`)

## Networking

- Use internal networks for backend services
- Never expose database ports to host in production
- Use Compose network aliases for service discovery
- Prefer host networking only for development

## Dockerfile Best Practices

- Order layers by cache frequency (least → most changing)
- Combine RUN commands to reduce layers
- Use `--no-cache` for apt/apk installs
- Copy only what's needed (use `.dockerignore`)
- Label images with version, date, and commit SHA
