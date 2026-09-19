# Docker Commands Cheat Sheet

> Essential Docker container lifecycle, image optimization, multi-stage builds, networking, storage volumes, and compose commands based on engineering modules.

## 1. Docker Host Setup & Daemon Operations

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `docker version` | Displays client and server (daemon) engine versions, API versions, Go version, Git commit, and OS/architecture. Used to verify API compatibility. | None | Daemon, Version |
| `docker info` | Displays comprehensive system-wide information including total containers (running, paused, stopped), image count, storage driver (overlay2), and cgroup driver. | None | Host Info, Diagnostics |
| `sudo usermod -aG docker $USER` | Appends current user to the `docker` unix group, granting access to the `/var/run/docker.sock` UNIX domain socket without requiring sudo privileges. | `-a` (append), `-G` (group) | Permissions, Host Security |
| `systemctl status docker` | Checks the status of the Docker systemd daemon process (`dockerd`). The primary service to inspect when Docker CLI commands return socket errors. | None | Systemd, Daemon |

## 2. Container Lifecycle & Execution

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `docker run -d --name web -p 8080:80 nginx:alpine` | Runs an Nginx container in detached background mode (`-d`), assigns a custom container name (`--name web`), and binds host port 8080 to container port 80. | `-d` (detached), `--name` (identifier), `-p` (port mapping) | Container, Runtime |
| `docker run -it --name debug-box ubuntu:22.04 /bin/bash` | Allocates a pseudo-TTY (`-t`) and keeps standard input open (`-i`), dropping you into an interactive Bash prompt inside a new Ubuntu container. | `-i` (interactive), `-t` (tty) | Interactive, Shell |
| `docker run --rm -it alpine sh` | Launches a lightweight Alpine shell and automatically removes (`--rm`) the container and its anonymous filesystem upon exiting. Perfect for quick one-off tasks. | `--rm` (auto remove on exit), `-it` (interactive tty) | Disposable, Testing |
| `docker ps` | Lists all currently active, running containers with Container ID, Image, Command, Creation time, Status, Ports, and Names. | None | Containers, Active |
| `docker ps -a` | Lists all containers regardless of state (Running, Exited, Created, Dead). Crucial for diagnosing containers that fail immediately upon startup. | `-a` (--all) | Containers, History |
| `docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"` | Formats container listing into clean tabular output using Go templates, omitting long commands for maximum terminal readability. | `--format` (Go template) | Formatting, CLI |
| `docker stop <container_id>` | Gracefully stops a running container by sending SIGTERM to PID 1, waiting 10 seconds for clean shutdown, then issuing SIGKILL if still running. | `SIGTERM` followed by `SIGKILL` | Lifecycle, Shutdown |
| `docker start -i <container_id>` | Starts a previously stopped container and immediately attaches interactive STDIN/STDOUT (`-i`), reopening an interactive session without spawning a new container. | `-i` (interactive attach) | Lifecycle, Restart |
| `docker restart <container_id>` | Restarts a container by stopping it and immediately launching it again. Frequently used after modifying bind-mounted configuration files. | None | Lifecycle, Reboot |
| `docker rm <container_id>` | Permanently removes a stopped container and its writable container layer. | None | Cleanup, Removal |
| `docker rm -f <container_id>` | Forcefully terminates a running container via SIGKILL and deletes it in a single atomic operation. | `-f` (force removal) | Cleanup, Force |

## 3. Container Shell, Exec & Process Inspection

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `docker exec -it <container_id> /bin/bash` | Spawns a new process (`/bin/bash`) inside an existing running container with an interactive pseudo-TTY. Standard industry practice for live debugging. | `-i` (interactive), `-t` (tty) | Debugging, Exec |
| `docker exec -u root <container_id> whoami` | Executes a command inside the container as a specific user (e.g. `root`), bypassing the default unprivileged container user for administrative tasks. | `-u` (user override) | Exec, Privileges |
| `docker attach <container_id>` | Attaches local standard input/output/error streams to the container's PID 1 process. To detach without stopping container, use `Ctrl+P, Ctrl+Q`. | None | Console, Process 1 |
| `docker top <container_id> -ef` | Displays host-level processes running inside the container namespace without having to enter the container. Shows actual host PIDs. | `-ef` (ps syntax) | Security, Process Audit |
| `docker cp <container_id>:/var/log/app.log ./local_logs/` | Copies files or directories bidirectionally between a container (running or stopped) and the host filesystem for post-mortem analysis. | `container:src host:dst` | Filesystem, Log Extract |

## 4. Container Logs & Live Telemetry

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `docker logs -f --tail 100 <container_id>` | Streams real-time standard output and standard error logs (`-f`), outputting only the last 100 log lines to avoid terminal flooding. | `-f` (follow), `--tail` (line count) | Logs, Streaming |
| `docker logs -t --since "15m" <container_id>` | Prints container logs generated in the last 15 minutes with human-readable RFC3339 timestamps (`-t`) for precise incident timeframe analysis. | `-t` (timestamps), `--since` (time window) | Logs, Incident Analysis |
| `docker stats --no-stream` | Captures a one-time snapshot of live CPU %, memory usage/limits, network I/O, and block I/O across all running containers. | `--no-stream` (single snapshot) | Performance, Metrics |
| `docker inspect <container_id>` | Returns low-level JSON configuration and state metadata for a container, including network settings, mounts, environment variables, and health checks. | JSON array output | Inspection, Metadata |
| `docker inspect <container_id> \| jq '.[0].NetworkSettings.IPAddress'` | Parses container JSON metadata using `jq` to extract the assigned internal Docker bridge network IP address directly. | Piped through `jq` | Networking, IP Address |

## 5. Image Management & BuildKit

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `docker build -t myapp:1.0 .` | Compiles the `Dockerfile` located in the current directory (`.`) into a tagged image `myapp:1.0` using the local directory as the build context. | `-t` (tag `name:version`), `.` (context) | Build, Images |
| `docker build -f Dockerfile.prod -t myapp:prod .` | Builds an image specifying a custom Dockerfile path (`-f Dockerfile.prod`) instead of the default `Dockerfile`. | `-f` (file path) | Build, Production |
| `docker build --no-cache -t myapp:clean .` | Forces Docker to rebuild all layers from scratch, bypassing layer caching. Crucial when pulling updated base images or OS security packages. | `--no-cache` (disable cache) | Build, Security |
| `docker buildx build --platform linux/amd64,linux/arm64 -t repo/app:1.0 --push .` | Uses BuildKit buildx to create multi-architecture container images for both Intel/AMD64 and Apple Silicon/ARM64 and pushes directly to registry. | `--platform` (arch targets), `--push` (upload) | Buildx, Multi-Arch |
| `docker images` | Lists all locally stored Docker images with Repository, Tag, Image ID, Creation date, and Virtual Size. | Alias for `docker image ls` | Images, Inventory |
| `docker rmi <image_id>` | Removes one or more images from local Docker host storage if no containers are currently referencing them. | None | Cleanup, Images |
| `docker tag local_app:1.0 docker.io/username/app:1.0` | Creates a new alias/tag pointing to an existing image ID, preparing it for authentication and push to a remote container registry. | `source_image target_reference` | Registry, Tagging |
| `docker push docker.io/username/app:1.0` | Uploads a tagged image and its layer blobs to a remote container registry (Docker Hub, AWS ECR, GitHub Packages). | None | Registry, CI/CD |
| `docker history <image_id>` | Displays the chronological layer history of an image, showing which Dockerfile instruction created each layer and its uncompressed disk size. | None | Optimization, Layers |
| `docker save -o myapp.tar myapp:1.0 && docker load -i myapp.tar` | Exports an image to an uncompressed or gzipped tarball, and loads it back into Docker on an air-gapped machine without external internet access. | `-o` (output file), `-i` (input file) | Migration, Air-Gapped |

## 6. Storage: Named Volumes & Bind Mounts

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `docker volume create pg_data` | Creates a Docker-managed named volume stored under `/var/lib/docker/volumes/` on the host, isolated from container lifecycles. | None | Storage, Volumes |
| `docker volume ls` | Lists all Docker-managed volumes on the host system. | None | Storage, Volumes |
| `docker volume inspect pg_data` | Inspects volume metadata including Mountpoint directory on the host filesystem and volume driver (default: `local`). | None | Storage, Inspection |
| `docker run -d --name db -v pg_data:/var/lib/postgresql/data postgres:16` | Mounts the named volume `pg_data` to `/var/lib/postgresql/data` inside the container. Data persists even if container is destroyed. | `-v <vol_name>:<container_path>` | Persistence, Database |
| `docker run -d --name web -v $(pwd)/html:/usr/share/nginx/html:ro nginx` | Mounts the host directory `$(pwd)/html` directly into the container as read-only (`:ro`), preventing the container from modifying host files. | `-v <host_path>:<container_path>:ro` | Bind Mount, Read-Only |
| `docker volume rm <vol_name>` | Removes an unused named volume. Will fail if any container (even stopped) is currently attached to it. | None | Storage, Cleanup |
| `docker volume prune` | Permanently removes all anonymous and unused named volumes not referenced by any container, reclaiming disk capacity. | None | Maintenance, Volumes |

## 7. Container Networking

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `docker network ls` | Lists all Docker networks on the host, showing Network ID, Name, Driver (`bridge`, `host`, `none`, `overlay`), and Scope. | None | Networking, Inventory |
| `docker network create --driver bridge app-net` | Creates a custom bridge network with built-in embedded DNS server, enabling containers to communicate using container names as hostnames. | `--driver bridge` (custom bridge) | Networking, DNS |
| `docker run -d --name backend --network app-net my-api` | Launches a container attached to the `app-net` network. Other containers on `app-net` can resolve this service using `http://backend`. | `--network <net_name>` | Networking, Discovery |
| `docker network connect app-net old-container` | Connects a currently running container to an additional Docker network dynamically without restarting it. | `network_name container_id` | Networking, Multi-Homed |
| `docker network inspect app-net` | Returns detailed JSON listing of subnet CIDRs, gateway IP, and all containers connected with their assigned IP and MAC addresses. | None | Networking, Inspection |
| `docker network prune` | Removes all custom Docker networks that are not currently utilized by at least one container. | None | Networking, Cleanup |

## 8. Docker Compose Multi-Container Stacks

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `docker compose up -d` | Reads `docker-compose.yml`, builds/pulls missing images, creates dedicated bridge network and volumes, and starts all services in the background. | `-d` (detached) | Compose, Deployment |
| `docker compose up -d --build` | Forces a rebuild of images before starting services. Crucial when application source code or Dockerfiles have changed. | `--build` (force build) | Compose, Rebuild |
| `docker compose down` | Gracefully stops and removes all containers, networks, and internal resources created by `docker compose up`. | None | Compose, Tear Down |
| `docker compose down -v` | Stops containers, tears down networks, and permanently destroys associated named volumes. Resets environment to clean state. | `-v` (delete named volumes) | Compose, Reset |
| `docker compose ps` | Displays status of all containers belonging to the current Compose project, showing service name, state, and exposed ports. | None | Compose, Status |
| `docker compose logs -f <service_name>` | Follows (-f) aggregated or service-specific logs across the Compose stack with color-coded service prefixes. | `-f` (follow), `<service>` | Compose, Logs |
| `docker compose exec <service_name> sh` | Runs an interactive shell inside the primary container running the specified Compose service. | None | Compose, Exec |
| `docker compose restart <service_name>` | Restarts a single service container in the multi-tier Compose stack without interrupting dependent services. | None | Compose, Restart |

## 9. System Maintenance, Pruning & Disk Cleanup

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `docker system df` | Displays a summary of Docker disk space usage broken down by Images, Containers, Local Volumes, and Build Cache with reclaimable percentages. | None | Storage, Diagnostics |
| `docker system prune -af --volumes` | Reclaims massive disk space by forcefully purging all stopped containers, unused networks, dangling + unreferenced images, and anonymous volumes. | `-a` (all unused), `-f` (force), `--volumes` | Cleanup, Emergency |
| `docker image prune -a` | Removes all unused images (both dangling `<none>` images and images not actively running in at least one container). | `-a` (all unreferenced) | Cleanup, Images |
| `docker ps -aq \| xargs docker rm -f` | Forcefully terminates and removes all containers on the host system in one command. Used to clear testing environments. | `-q` (quiet IDs only), `xargs` | Cleanup, Bulk |
