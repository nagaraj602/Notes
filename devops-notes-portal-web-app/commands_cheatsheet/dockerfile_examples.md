# Dockerfile Production Examples

> Highly optimized, secure, multi-stage and distroless Dockerfiles for Node.js, Java Spring Boot, Python FastAPI, and Go.

## 1. Multi-Stage Java Spring Boot Application Dockerfile with Distroless
**Description**: Compiles Maven project inside an OpenJDK container and copies only the executed jar into a minimal Google Distroless runtime image, eliminating OS utilities and package managers for maximum security.

```dockerfile
# ------------------------------------------------------------
# Stage 1: Build & Dependency Packaging
# ------------------------------------------------------------
FROM maven:3.9.6-eclipse-temurin-17-alpine AS builder

WORKDIR /build

# Cache Maven dependencies layer
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Compile and package application
COPY src/ ./src/
RUN mvn clean package -DskipTests=true

# ------------------------------------------------------------
# Stage 2: Minimal Distroless Java Runtime
# ------------------------------------------------------------
FROM gcr.io/distroless/java17-debian12:nonroot

WORKDIR /app

# Run as non-root user (distroless nonroot UID is 65532)
USER nonroot:nonroot

# Copy compiled JAR artifact from builder stage
COPY --from=builder --chown=nonroot:nonroot /build/target/*.jar app.jar

ENV JAVA_OPTS="-XX:+UseG1GC -XX:MaxRAMPercentage=75.0 -Djava.security.egd=file:/dev/./urandom"
ENV SERVER_PORT=8080

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

## 2. Multi-Stage Node.js React Production Dockerfile with Nginx Alpine
**Description**: Builds frontend static assets using Node.js and serves them using a hardened Nginx Alpine web server image (~25MB total size).

```dockerfile
# ------------------------------------------------------------
# Stage 1: Node.js Asset Builder
# ------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Cache package dependencies layer
COPY package.json package-lock.json ./
RUN npm ci --prefer-offline

COPY . .
RUN npm run build

# ------------------------------------------------------------
# Stage 2: Nginx Web Server Runtime
# ------------------------------------------------------------
FROM nginx:1.25-alpine-slim

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Run as unprivileged nginx user
RUN touch /var/run/nginx.pid &&     chown -R nginx:nginx /var/run/nginx.pid /usr/share/nginx/html /var/cache/nginx

USER nginx

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --retries=3   CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

## 3. Python FastAPI Production Container with Non-Root User
**Description**: Python 3.11 slim image utilizing wheels and multi-stage build to remove gcc build tools from the final runtime container.

```dockerfile
# ------------------------------------------------------------
# Stage 1: Builder
# ------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ------------------------------------------------------------
# Stage 2: Minimal Final Image
# ------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Copy installed python libraries from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

COPY --chown=appuser:appuser app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```
