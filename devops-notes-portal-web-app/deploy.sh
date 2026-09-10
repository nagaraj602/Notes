#!/usr/bin/env bash
# ==============================================================================
#  🚀 DevOps Knowledge Portal & Interview Hub - Universal Deployment Script
#  Compatible with: Git Bash (Windows), Ubuntu / Debian (Linux / GCP VM), macOS
# ==============================================================================

set -eo pipefail

# Text styling
BOLD="\033[1m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
RED="\033[1;31m"
RESET="\033[0m"

# Default configuration
DEFAULT_IMAGE_NAME="nagarajkamath602/devops-hub-notes-artisantek-training-mterial-interview-questions"
DEFAULT_TAG="latest"
K8S_MANIFEST="k8s/all-in-one.yaml"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

# Detect OS
OS="Unknown"
if [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* || "$OSTYPE" == "win32"* ]]; then
    OS="Windows (Git Bash)"
elif [[ "$OSTYPE" == "linux"* ]]; then
    OS="Linux ($(grep -oP '(?<=^ID=).+' /etc/os-release 2>/dev/null | tr -d '"' || echo 'Generic'))"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
fi

print_header() {
    clear 2>/dev/null || true
    echo -e "${CYAN}========================================================================${RESET}"
    echo -e "${BOLD}     🚀 DevOps Knowledge Portal & Interview Hub Deployer${RESET}"
    echo -e "${CYAN}========================================================================${RESET}"
    echo -e " Environment : ${GREEN}$OS${RESET}"
    echo -e " Directory   : ${YELLOW}$APP_DIR${RESET}"
    echo -e " Image Target: ${YELLOW}$DEFAULT_IMAGE_NAME:$DEFAULT_TAG${RESET}"
    echo -e "${CYAN}========================================================================${RESET}\n"
}

# ------------------------------------------------------------------------------
# Helper: Push image with Docker Hub account authorization verification
# ------------------------------------------------------------------------------
push_with_auth_check() {
    local img="$1"
    local repo_user="${img%%/*}"

    echo -e "\n${CYAN}==> Attempting to push image: ${YELLOW}$img${RESET}..."
    
    # Try pushing and capture both output and exit status
    set +e
    push_output=$(docker push "$img" 2>&1)
    push_exit=$?
    set -e

    if [ $push_exit -eq 0 ]; then
        echo -e "${GREEN}✔ Image successfully pushed: $img${RESET}"
        return 0
    fi

    # Push failed - check for permission/authentication errors
    echo -e "\n${RED}✘ Failed to push image to Docker Hub!${RESET}"
    echo -e "${YELLOW}Docker Output:${RESET}"
    echo "$push_output" | sed 's/^/  /'

    if echo "$push_output" | grep -Ei "denied|unauthorized|authentication required|requested access" > /dev/null; then
        echo -e "\n${YELLOW}------------------------------------------------------------------------${RESET}"
        echo -e "${BOLD}${RED}⚠️  AUTHENTICATION / PERMISSION ISSUE DETECTED${RESET}"
        echo -e "You are pushing to repository owned by: ${CYAN}$repo_user${RESET}"
        echo -e "You may currently be logged into a ${RED}different Docker Hub account${RESET}."
        echo -e "${YELLOW}------------------------------------------------------------------------${RESET}"
        
        read -p "Would you like to log in to Docker Hub as '$repo_user' now? (Y/n): " do_login
        do_login=${do_login:-Y}
        if [[ "$do_login" =~ ^[Yy]$ ]]; then
            echo -e "\n${CYAN}Running 'docker login' for user '${repo_user}'...${RESET}"
            docker login -u "$repo_user"
            
            echo -e "\n${CYAN}Retrying push to ${YELLOW}$img${CYAN}...${RESET}"
            if docker push "$img"; then
                echo -e "${GREEN}✔ Image successfully pushed on retry: $img${RESET}"
                return 0
            else
                echo -e "${RED}✘ Push failed again. Please verify your repository permissions.${RESET}"
                return 1
            fi
        else
            echo -e "${YELLOW}Skipping re-login. The image was built locally but not pushed.${RESET}"
            return 1
        fi
    else
        echo -e "${RED}Unknown push error occurred. Please check network connectivity.${RESET}"
        return 1
    fi
}

# ------------------------------------------------------------------------------
# 1. Docker Compose Deployment
# ------------------------------------------------------------------------------
deploy_docker_compose() {
    echo -e "\n${CYAN}------------------------------------------------------------${RESET}"
    echo -e "${BOLD}  [1] Docker Compose Deployment${RESET}"
    echo -e "${CYAN}------------------------------------------------------------${RESET}"

    echo "Choose build / pull mode:"
    echo "  1) Pull prebuilt image from Docker Hub (Fastest, best for GCP/Remote servers)"
    echo "  2) Build Docker image locally (Best for local code testing & development)"
    read -p "Select [1 or 2] (Default: 1): " compose_mode
    compose_mode=${compose_mode:-1}

    if [ "$compose_mode" == "2" ]; then
        echo -e "\n${CYAN}==> Building Docker image locally...${RESET}"
        docker compose build
        
        read -p "Do you want to push this newly built image to Docker Hub? (y/N): " do_push
        if [[ "$do_push" =~ ^[Yy]$ ]]; then
            push_with_auth_check "$DEFAULT_IMAGE_NAME:$DEFAULT_TAG"
        fi
    else
        echo -e "\n${CYAN}==> Pulling latest image from Docker Hub...${RESET}"
        docker compose pull devops-hub || {
            echo -e "${YELLOW}Warning: Pull failed, attempting local build fallback...${RESET}"
            docker compose build
        }
    fi

    echo -e "\n${CYAN}==> Stopping any previous container...${RESET}"
    docker compose down --remove-orphans || true

    echo -e "\n${CYAN}==> Starting devops-hub with Docker Compose...${RESET}"
    docker compose up -d

    echo -e "\n${GREEN}✔ Container started! Current status:${RESET}"
    docker compose ps

    echo -e "\n${CYAN}==> Verifying health status (waiting 5s)...${RESET}"
    sleep 5
    if command -v curl &>/dev/null; then
        if curl -s -f http://localhost:8000/api/health > /dev/null; then
            echo -e "${GREEN}✔ Health Check Passed! (http://localhost:8000/api/health)${RESET}"
        elif curl -s -f http://localhost:80/api/health > /dev/null; then
            echo -e "${GREEN}✔ Health Check Passed on Port 80! (http://localhost:80/api/health)${RESET}"
        else
            echo -e "${YELLOW}ℹ Container is still initializing git repositories. Run 'docker compose logs -f' to monitor.${RESET}"
        fi
    fi

    echo -e "\n${GREEN}========================================================================${RESET}"
    echo -e " DevOps Hub is now accessible at:"
    echo -e "   • Port 8000: ${CYAN}http://localhost:8000${RESET} (or http://<SERVER_IP>:8000)"
    echo -e "   • Port 80  : ${CYAN}http://localhost:80${RESET}   (or http://<SERVER_IP>)"
    echo -e "   • Interview Hub: ${CYAN}http://localhost:8000/interviews${RESET}"
    echo -e "${GREEN}========================================================================${RESET}"
}

# ------------------------------------------------------------------------------
# 2. Docker Desktop Kubernetes
# ------------------------------------------------------------------------------
deploy_docker_desktop_k8s() {
    echo -e "\n${CYAN}------------------------------------------------------------${RESET}"
    echo -e "${BOLD}  [2] Docker Desktop Kubernetes Deployment${RESET}"
    echo -e "${CYAN}------------------------------------------------------------${RESET}"

    if ! command -v kubectl &>/dev/null; then
        echo -e "${RED}✘ 'kubectl' command not found. Please install kubectl or enable Kubernetes in Docker Desktop.${RESET}"
        return 1
    fi

    current_ctx=$(kubectl config current-context 2>/dev/null || echo "none")
    echo -e "Current kubectl context: ${YELLOW}$current_ctx${RESET}"

    read -p "Do you want to rebuild and push the Docker image before deploying? (y/N): " do_rebuild
    if [[ "$do_rebuild" =~ ^[Yy]$ ]]; then
        echo -e "\n${CYAN}==> Building Docker images...${RESET}"
        docker build -t "$DEFAULT_IMAGE_NAME:$DEFAULT_TAG" -t "$DEFAULT_IMAGE_NAME:v6.6.3" .
        push_with_auth_check "$DEFAULT_IMAGE_NAME:$DEFAULT_TAG"
        push_with_auth_check "$DEFAULT_IMAGE_NAME:v6.6.3"
    fi

    echo -e "\n${CYAN}==> Applying Kubernetes manifests from $K8S_MANIFEST...${RESET}"
    kubectl apply -f "$K8S_MANIFEST"

    echo -e "\n${CYAN}==> Waiting for deployment rollout...${RESET}"
    kubectl rollout status deployment/devops-hub-deployment -n devops-hub --timeout=120s || true

    echo -e "\n${GREEN}✔ Kubernetes Resources Status:${RESET}"
    kubectl get pods,svc,pvc -n devops-hub

    echo -e "\n${GREEN}========================================================================${RESET}"
    echo -e " Docker Desktop routes LoadBalancer directly to localhost!"
    echo -e " Access the portal at:"
    echo -e "   • Web Portal   : ${CYAN}http://localhost:8000${RESET}"
    echo -e "   • NodePort     : ${CYAN}http://localhost:30080${RESET}"
    echo -e "   • Interview Hub: ${CYAN}http://localhost:8000/interviews${RESET}"
    echo -e "${GREEN}========================================================================${RESET}"
}

# ------------------------------------------------------------------------------
# 3. Kubeadm / Production Kubernetes Cluster Deployment
# ------------------------------------------------------------------------------
deploy_kubeadm() {
    echo -e "\n${CYAN}------------------------------------------------------------${RESET}"
    echo -e "${BOLD}  [3] Kubeadm / Production Kubernetes Deployment${RESET}"
    echo -e "${CYAN}------------------------------------------------------------${RESET}"

    if ! command -v kubectl &>/dev/null; then
        echo -e "${RED}✘ 'kubectl' command not found. Ensure KUBECONFIG is exported.${RESET}"
        return 1
    fi

    echo -e "${CYAN}==> Checking Cluster Info...${RESET}"
    kubectl cluster-info || {
        echo -e "${RED}✘ Cannot connect to Kubernetes API server. Check your ~/.kube/config.${RESET}"
        return 1
    }

    echo -e "\n${CYAN}==> Applying Kubernetes manifests ($K8S_MANIFEST)...${RESET}"
    kubectl apply -f "$K8S_MANIFEST"

    echo -e "\n${CYAN}==> Monitoring deployment rollout in 'devops-hub' namespace...${RESET}"
    kubectl rollout status deployment/devops-hub-deployment -n devops-hub --timeout=120s

    echo -e "\n${GREEN}✔ Deployed Pods & Services:${RESET}"
    kubectl get pods,svc,pvc -n devops-hub -o wide

    echo -e "\n${YELLOW}📌 Accessing on Kubeadm Cluster:${RESET}"
    echo "  1) NodePort Access: The service exposes NodePort 30080."
    echo -e "     Access at: ${CYAN}http://<ANY_WORKER_NODE_IP>:30080${RESET}"
    echo "  2) Port-Forward (Quick check):"
    echo -e "     ${YELLOW}kubectl port-forward -n devops-hub svc/devops-hub-service 8000:8000${RESET}"
    echo "  3) For Cloud/MetalLB: Check external IP in 'kubectl get svc -n devops-hub'."
}

# ------------------------------------------------------------------------------
# 4. Standalone Docker Run
# ------------------------------------------------------------------------------
deploy_docker_run() {
    echo -e "\n${CYAN}------------------------------------------------------------${RESET}"
    echo -e "${BOLD}  [4] Standalone Docker Run Container${RESET}"
    echo -e "${CYAN}------------------------------------------------------------${RESET}"

    CONTAINER_NAME="devops-hub"
    read -p "Enter container name (Default: devops-hub): " input_cname
    CONTAINER_NAME=${input_cname:-devops-hub}

    read -p "Enter image to run (Default: $DEFAULT_IMAGE_NAME:$DEFAULT_TAG): " input_img
    IMAGE_TO_RUN=${input_img:-"$DEFAULT_IMAGE_NAME:$DEFAULT_TAG"}

    echo -e "\n${CYAN}==> Pulling image $IMAGE_TO_RUN...${RESET}"
    docker pull "$IMAGE_TO_RUN"

    if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}\$"; then
        echo -e "${YELLOW}Stopping and removing existing '$CONTAINER_NAME' container...${RESET}"
        docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
        docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
    fi

    echo -e "\n${CYAN}==> Running container '$CONTAINER_NAME'...${RESET}"
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p 80:8000 \
        -p 8000:8000 \
        -v devops_hub_notes_data:/app/data/notes \
        -e REPO_URL="https://github.com/nagaraj602/Notes.git" \
        -e REPO_BRANCH="main" \
        -e AUTO_SYNC_INTERVAL_MINUTES=5 \
        --restart unless-stopped \
        "$IMAGE_TO_RUN"

    echo -e "\n${GREEN}✔ Container started!${RESET}"
    docker ps --filter "name=$CONTAINER_NAME"
}

# ------------------------------------------------------------------------------
# 5. GCP Ubuntu Full Automated Setup (Install Docker + Deploy + Cloudflare)
# ------------------------------------------------------------------------------
deploy_gcp_ubuntu_full() {
    echo -e "\n${CYAN}------------------------------------------------------------${RESET}"
    echo -e "${BOLD}  [5] GCP Ubuntu Full Setup (Docker + App + Cloudflare Tunnel)${RESET}"
    echo -e "${CYAN}------------------------------------------------------------${RESET}"

    if [[ "$OSTYPE" != "linux"* ]]; then
        echo -e "${YELLOW}Notice: This option is designed to run directly on an Ubuntu/Debian Linux server (e.g. GCP VM).${RESET}"
        read -p "Continue anyway? (y/N): " cont
        if [[ ! "$cont" =~ ^[Yy]$ ]]; then return 0; fi
    fi

    # Step 1: Install Docker if missing
    if ! command -v docker &>/dev/null; then
        echo -e "\n${CYAN}==> Docker not found. Installing Docker engine...${RESET}"
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        rm -f get-docker.sh
        sudo usermod -aG docker "$USER" 2>/dev/null || true
        sudo systemctl enable --now docker
        echo -e "${GREEN}✔ Docker installed successfully!${RESET}"
    else
        echo -e "${GREEN}✔ Docker is already installed.${RESET}"
    fi

    # Step 2: Ensure Docker Compose is available
    if ! docker compose version &>/dev/null; then
        echo -e "\n${CYAN}==> Installing Docker Compose plugin...${RESET}"
        sudo apt-get update && sudo apt-get install -y docker-compose-plugin
    fi

    # Step 3: Deploy Application via Docker Compose
    echo -e "\n${CYAN}==> Deploying DevOps Hub via Docker Compose...${RESET}"
    docker compose pull devops-hub || true
    docker compose down --remove-orphans || true
    docker compose up -d

    echo -e "\n${GREEN}✔ Application container running!${RESET}"
    docker compose ps

    # Step 4: Cloudflare Tunnel Setup (No inbound ports needed!)
    echo -e "\n${CYAN}------------------------------------------------------------${RESET}"
    echo -e "${BOLD}Cloudflare Tunnel Configuration (Zero Open Ports on GCP)${RESET}"
    echo -e "${CYAN}------------------------------------------------------------${RESET}"
    echo "Cloudflare Tunnel allows you to access this application securely over HTTPS"
    echo "WITHOUT opening port 80 or 8000 in GCP VPC Firewall or VM firewalls!"
    echo ""
    echo "Select Cloudflare option:"
    echo "  1) Quick Tunnel (Free, instant https://xxxx.trycloudflare.com, no domain needed)"
    echo "  2) Cloudflare Zero Trust Named Tunnel (Permanent custom domain with Token)"
    echo "  3) Skip Cloudflare Tunnel (Use standard GCP public IP with open firewall)"
    read -p "Select [1, 2, or 3] (Default: 1): " cf_choice
    cf_choice=${cf_choice:-1}

    setup_cloudflare_tunnel "$cf_choice"
}

# ------------------------------------------------------------------------------
# 6. Cloudflare Tunnel Installer & Runner
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# 6. Cloudflare Tunnel Installer & Runner
# ------------------------------------------------------------------------------
show_cloudflare_token_guide() {
    echo -e "\n${CYAN}========================================================================${RESET}"
    echo -e "${BOLD} 📖 How to Generate Your Cloudflare Tunnel Token (Step-by-Step)${RESET}"
    echo -e "${CYAN}========================================================================${RESET}"
    echo -e " ${BOLD}Prerequisite:${RESET} A free Cloudflare account with a domain added to it."
    echo ""
    echo -e " ${BOLD}Step 1:${RESET} Open the Cloudflare Zero Trust Dashboard in your browser:"
    echo -e "         👉 ${CYAN}https://one.dash.cloudflare.com${RESET}"
    echo -e "         (If it is your first time, create a free Team name and pick the \$0 Plan)"
    echo ""
    echo -e " ${BOLD}Step 2:${RESET} In the left sidebar, click ${YELLOW}Networks${RESET} ➔ ${YELLOW}Tunnels${RESET}."
    echo ""
    echo -e " ${BOLD}Step 3:${RESET} Click the ${GREEN}'Add a tunnel'${RESET} (or 'Create a tunnel') button."
    echo ""
    echo -e " ${BOLD}Step 4:${RESET} Select connector type: ${BOLD}'Cloudflared'${RESET} and click ${CYAN}'Next'${RESET}."
    echo ""
    echo -e " ${BOLD}Step 5:${RESET} Name your tunnel (e.g. ${YELLOW}devops-hub-gcp${RESET}) and click ${CYAN}'Save tunnel'${RESET}."
    echo ""
    echo -e " ${BOLD}Step 6:${RESET} On the 'Install and run a connector' page:"
    echo -e "         • Operating system: Click ${BOLD}Debian${RESET} (for Ubuntu/Debian on GCP)"
    echo -e "         • Architecture    : Click ${BOLD}64-bit${RESET}"
    echo -e "         • Cloudflare will display a command box with:"
    echo -e "           ${YELLOW}sudo cloudflared service install eyJhIjoi...${RESET}"
    echo -e "           (or 'cloudflared tunnel run --token eyJhIjoi...')"
    echo ""
    echo -e " ${BOLD}Step 7:${RESET} Copy that command (or just the eyJh... token) and paste it into this script!"
    echo ""
    echo -e " ${BOLD}Step 8:${RESET} Once installed, click ${CYAN}'Next'${RESET} in Cloudflare to add a ${BOLD}Public Hostname${RESET}:"
    echo -e "         • Subdomain : e.g. ${YELLOW}notes${RESET} (gives you notes.yourdomain.com)"
    echo -e "         • Domain    : Select your domain from the dropdown"
    echo -e "         • Service Type: Select ${BOLD}HTTP${RESET}"
    echo -e "         • URL       : Enter ${BOLD}localhost:8000${RESET}"
    echo -e "         • Click ${GREEN}'Save hostname'${RESET}"
    echo ""
    echo -e " 🎉 That is it! Your app is live at ${CYAN}https://notes.yourdomain.com${RESET} with zero open GCP ports!"
    echo -e "${CYAN}========================================================================${RESET}\n"
}

setup_cloudflare_tunnel() {
    local choice="$1"

    if [ -z "$choice" ]; then
        echo -e "\n${CYAN}------------------------------------------------------------${RESET}"
        echo -e "${BOLD}  [6] Cloudflare Tunnel Setup (Zero GCP Port Exposure)${RESET}"
        echo -e "${CYAN}------------------------------------------------------------${RESET}"
        echo "  1) Quick Tunnel (Free, instant https://xxxx.trycloudflare.com, no domain needed)"
        echo "  2) Cloudflare Zero Trust Named Tunnel (Permanent custom domain with Token)"
        echo "  3) 📖 Show Step-by-Step Guide: How to Generate Tunnel Token in Cloudflare"
        echo "  4) Check running Cloudflare Tunnel status"
        read -p "Select [1, 2, 3, or 4] (Default: 1): " choice
        choice=${choice:-1}
    fi

    if [ "$choice" == "3" ]; then
        show_cloudflare_token_guide
        read -p "Press [Enter] to return to Cloudflare tunnel setup..." dummy
        setup_cloudflare_tunnel ""
        return 0
    fi

    if [ "$choice" == "4" ]; then
        if command -v systemctl &>/dev/null && systemctl list-unit-files | grep -q cloudflared; then
            sudo systemctl status cloudflared --no-pager
        else
            echo "No systemd cloudflared service found. Checking active processes:"
            ps aux | grep cloudflared | grep -v grep || echo "No cloudflared process running."
        fi
        return 0
    fi

    # Install cloudflared binary if missing
    if ! command -v cloudflared &>/dev/null; then
        echo -e "\n${CYAN}==> Installing cloudflared...${RESET}"
        if [[ "$OSTYPE" == "linux"* ]]; then
            ARCH="amd64"
            if [ "$(uname -m)" == "aarch64" ]; then ARCH="arm64"; fi
            curl -fsSL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}.deb" -o /tmp/cloudflared.deb
            sudo dpkg -i /tmp/cloudflared.deb || sudo apt-get install -f -y
            rm -f /tmp/cloudflared.deb
        elif [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* ]]; then
            echo -e "${YELLOW}On Windows, please download cloudflared.exe from Cloudflare or install via winget:${RESET}"
            echo "  winget install --id Cloudflare.cloudflared"
            return 0
        fi
        echo -e "${GREEN}✔ cloudflared installed!${RESET}"
    fi

    if [ "$choice" == "1" ]; then
        echo -e "\n${GREEN}==> Starting Quick Cloudflare Tunnel for http://localhost:8000...${RESET}"
        echo -e "${YELLOW}Cloudflare will create a public HTTPS URL without touching GCP firewall!${RESET}"
        echo -e "${CYAN}Starting tunnel in background (logs saved to /tmp/cloudflared.log)...${RESET}"
        
        nohup cloudflared tunnel --url http://localhost:8000 > /tmp/cloudflared.log 2>&1 &
        sleep 5
        
        TUNNEL_URL=$(grep -o 'https://[-a-zA-Z0-9.]*\.trycloudflare\.com' /tmp/cloudflared.log | tail -n 1 || echo "")
        if [ -n "$TUNNEL_URL" ]; then
            echo -e "\n${GREEN}========================================================================${RESET}"
            echo -e " 🎉 YOUR APP IS LIVE SECURELY ON CLOUDFLARE TUNNEL:"
            echo -e "    ${BOLD}${CYAN}$TUNNEL_URL${RESET}"
            echo -e "    Interview Hub: ${CYAN}$TUNNEL_URL/interviews${RESET}"
            echo -e "${GREEN}========================================================================${RESET}"
        else
            echo -e "${YELLOW}Tunnel launched! Check URL by running:${RESET}"
            echo "  cat /tmp/cloudflared.log | grep trycloudflare.com"
        fi

    elif [ "$choice" == "2" ]; then
        echo -e "\n${CYAN}Named Tunnel Setup (Cloudflare Zero Trust Dashboard):${RESET}"
        echo -e "💡 ${YELLOW}Tip:${RESET} Type ${BOLD}'guide'${RESET} or ${BOLD}'g'${RESET} to read the step-by-step token creation guide."
        echo "Paste your token OR the full command from Cloudflare (e.g. 'sudo cloudflared service install eyJh...' or 'eyJh...'):"
        read -p "Tunnel Token / Command: " cf_token
        
        clean_input=$(echo "$cf_token" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e "s/^['\"]//" -e "s/['\"]$//")
        
        if [[ "$clean_input" =~ ^(g|guide|help)$ ]]; then
            show_cloudflare_token_guide
            read -p "Paste your token / command now: " cf_token
            clean_input=$(echo "$cf_token" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e "s/^['\"]//" -e "s/['\"]$//")
        fi

        # Auto-extract token if user pasted the full command or raw token
        if [[ "$clean_input" =~ (eyJh[A-Za-z0-9._-]+) ]]; then
            cf_token="${BASH_REMATCH[1]}"
        elif [[ "$clean_input" == *"service install "* ]]; then
            cf_token="${clean_input##*service install }"
            cf_token=$(echo "$cf_token" | awk '{print $1}')
        elif [[ "$clean_input" == *"--token "* ]]; then
            cf_token="${clean_input##*--token }"
            cf_token=$(echo "$cf_token" | awk '{print $1}')
        fi

        if [ -n "$cf_token" ]; then
            echo -e "\n${CYAN}==> Installing cloudflared system service with token...${RESET}"
            # Uninstall any stale service first to avoid collision
            sudo cloudflared service uninstall 2>/dev/null || true
            sudo cloudflared service install "$cf_token"
            sudo systemctl daemon-reload 2>/dev/null || true
            sudo systemctl enable --now cloudflared
            echo -e "${GREEN}✔ Cloudflare Tunnel service installed and running!${RESET}"
            sudo systemctl status cloudflared --no-pager || true
        else
            echo -e "${RED}No valid token found. Tunnel installation skipped.${RESET}"
        fi
    fi
}

# ------------------------------------------------------------------------------
# 7. Build & Push Image Only
# ------------------------------------------------------------------------------
build_and_push_image() {
    echo -e "\n${CYAN}------------------------------------------------------------${RESET}"
    echo -e "${BOLD}  [7] Build & Push Docker Image to Docker Hub${RESET}"
    echo -e "${CYAN}------------------------------------------------------------${RESET}"

    read -p "Enter version tag to build (Default: latest): " user_tag
    user_tag=${user_tag:-latest}

    TAGS=("-t" "$DEFAULT_IMAGE_NAME:$user_tag")
    if [ "$user_tag" != "latest" ]; then
        TAGS+=("-t" "$DEFAULT_IMAGE_NAME:latest")
    fi

    echo -e "\n${CYAN}==> Building multi-stage image for tag '${user_tag}'...${RESET}"
    docker build "${TAGS[@]}" .

    echo -e "\n${GREEN}✔ Build finished successfully!${RESET}"

    # Push tag
    push_with_auth_check "$DEFAULT_IMAGE_NAME:$user_tag"
    if [ "$user_tag" != "latest" ]; then
        push_with_auth_check "$DEFAULT_IMAGE_NAME:latest"
    fi
}

# ------------------------------------------------------------------------------
# 8. GCP VM 11 PM Shutdown & 6 AM Startup Scheduler
# ------------------------------------------------------------------------------
setup_gcp_schedule() {
    echo -e "\n${CYAN}------------------------------------------------------------${RESET}"
    echo -e "${BOLD}  [8] Schedule GCP VM Auto-Shutdown (11 PM) & Auto-Start (6 AM IST)${RESET}"
    echo -e "${CYAN}------------------------------------------------------------${RESET}"

    if ! command -v gcloud &>/dev/null; then
        echo -e "${RED}✘ 'gcloud' CLI is not installed or not in PATH.${RESET}"
        echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
        return 1
    fi

    read -p "Enter GCP VM Instance Name: " VM_NAME
    if [ -z "$VM_NAME" ]; then
        echo -e "${RED}VM Name is required.${RESET}"
        return 1
    fi

    read -p "Enter GCP Zone (Default: asia-south1-a): " VM_ZONE
    VM_ZONE=${VM_ZONE:-asia-south1-a}

    read -p "Enter GCP Region (Default: asia-south1): " VM_REGION
    VM_REGION=${VM_REGION:-asia-south1}

    SCHEDULE_NAME="devops-daily-schedule"

    echo -e "\n${CYAN}==> 1. Creating Resource Policy '$SCHEDULE_NAME'...${RESET}"
    gcloud compute resource-policies create instance-schedule "$SCHEDULE_NAME" \
        --region="$VM_REGION" \
        --vm-start-schedule="0 6 * * *" \
        --vm-stop-schedule="0 23 * * *" \
        --timezone="Asia/Kolkata" \
        --description="Daily auto-start at 6:00 AM IST and shutdown at 11:00 PM IST" || {
            echo -e "${YELLOW}Notice: Policy may already exist. Proceeding to attach...${RESET}"
        }

    echo -e "\n${CYAN}==> 2. Granting Compute Engine Service Account instanceAdmin role...${RESET}"
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)" 2>/dev/null || echo "")

    if [ -n "$PROJECT_NUMBER" ]; then
        SERVICE_ACCOUNT="service-${PROJECT_NUMBER}@compute-system.iam.gserviceaccount.com"
        gcloud projects add-iam-policy-binding "$PROJECT_ID" \
            --member="serviceAccount:${SERVICE_ACCOUNT}" \
            --role="roles/compute.instanceAdmin.v1" || true
    fi

    echo -e "\n${CYAN}==> 3. Attaching Schedule to VM '$VM_NAME'...${RESET}"
    gcloud compute instances add-resource-policies "$VM_NAME" \
        --zone="$VM_ZONE" \
        --resource-policies="$SCHEDULE_NAME"

    echo -e "\n${GREEN}✔ Successfully scheduled VM '$VM_NAME'!${RESET}"
    echo "  • Automatically starts at: 6:00 AM IST daily"
    echo "  • Automatically stops at : 11:00 PM IST daily"
}

# ------------------------------------------------------------------------------
# Main Menu Loop
# ------------------------------------------------------------------------------
while true; do
    print_header
    echo "Choose an action:"
    echo "  1) [Docker Compose] Deploy / update app using Docker Compose"
    echo "  2) [Docker Desktop K8s] Build, push & deploy to Docker Desktop Kubernetes"
    echo "  3) [Kubeadm Cluster] Deploy to production / multi-node Kubernetes cluster"
    echo "  4) [Docker Run] Run standalone container with persistent volume"
    echo "  5) [GCP Ubuntu Server Setup] Automated Setup (Docker + Compose + App + Cloudflare)"
    echo "  6) [Cloudflare Tunnel] Setup zero-port secure HTTPS tunnel"
    echo "  7) [Build & Push Only] Build image locally & push to Docker Hub (with auth fix)"
    echo "  8) [GCP VM Scheduler] Setup 11:00 PM Shutdown / 6:00 AM Startup Schedule"
    echo "  q) Quit"
    echo ""
    read -p "Select an option [1-8, q]: " choice

    case "$choice" in
        1) deploy_docker_compose ;;
        2) deploy_docker_desktop_k8s ;;
        3) deploy_kubeadm ;;
        4) deploy_docker_run ;;
        5) deploy_gcp_ubuntu_full ;;
        6) setup_cloudflare_tunnel ;;
        7) build_and_push_image ;;
        8) setup_gcp_schedule ;;
        q|Q) echo -e "\n${CYAN}Exiting. Happy DevOps coding!${RESET}\n"; exit 0 ;;
        *) echo -e "\n${RED}Invalid option. Please choose between 1 and 8.${RESET}" ;;
    esac

    echo ""
    read -p "Press [Enter] to return to the menu..." dummy
done
