# Docker Commands Cheat Sheet

> Essential Docker container lifecycle, image optimization, multi-stage builds, networking, and docker-compose commands.

| Command | Description & AI Explanation | Category / Tags |
| :--- | :--- | :--- |
| `docker build -t myapp:1.0 -f Dockerfile .` | Compiles Dockerfile in current directory into a tagged image named myapp:1.0 using local build context. | Images, Build |
| `docker buildx build --platform linux/amd64,linux/arm64 -t org/app:latest --push .` | Uses BuildKit buildx to create multi-architecture container images for both Intel/AMD and Apple Silicon/ARM and pushes directly to registry. | Buildx, Architecture |
| `docker run -d --name web -p 8080:80 --restart unless-stopped -v app-data:/data myapp:1.0` | Launches container in detached background mode (-d), binds host port 8080 to container port 80, sets restart policy, and mounts named volume app-data. | Runtime, Containers |
| `docker ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}\t{{.Names}}"` | Displays tabular listing of running and exited containers with custom column formatting for high readability. | Monitoring, Containers |
| `docker exec -it <container-id> /bin/sh` | Attaches an interactive TTY shell inside a running container for direct live debugging and filesystem inspection. | Debugging, Troubleshooting |
| `docker logs -f --tail 100 <container-name>` | Follows (-f) standard output and error streams of a container, initially outputting only the last 100 log lines. | Logs, Troubleshooting |
| `docker system prune -af --volumes` | Reclaims disk space by forcefully purging all unused containers, dangling images, unused networks, and build caches along with unused anonymous volumes. | Maintenance, Disk Cleanup |
| `docker inspect <container-id> \| jq '.[0].NetworkSettings.IPAddress'` | Inspects detailed JSON metadata of a container and extracts internal Docker bridge network IP address using jq. | Networking, Inspection |
| `docker stats --no-stream` | Captures a one-time snapshot of live CPU %, memory usage/limits, network I/O, and block I/O across all running containers. | Performance, Metrics |
| `docker compose -f docker-compose.yml up -d --build` | Re-builds changed container images and launches multi-service stack in the background defined in docker-compose.yml. | Compose, Orchestration |
| `docker compose down -v` | Stops and removes all containers, networks, and named volumes created by docker-compose, resetting to clean slate. | Compose, Clean-up |
| `docker save -o myimage.tar myapp:1.0 && docker load -i myimage.tar` | Archives a Docker image into a tarball and loads it on an air-gapped machine without external registry internet access. | Offline, Migration |
| `docker cp <container-id>:/app/logs/error.log ./local_logs/` | Copies a file from inside a running or stopped container directly to host filesystem for post-mortem analysis. | Troubleshooting, Filesystem |
| `docker top <container-id> -ef` | Displays host-level process IDs (PIDs) running inside the container namespace without having to enter the container. | Security, Process Audit |
