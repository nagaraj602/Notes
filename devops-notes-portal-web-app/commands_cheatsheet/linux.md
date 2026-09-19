# Linux Commands Cheat Sheet

> Comprehensive Linux administration, system performance diagnostics, networking, and troubleshooting reference based on engineering modules.

## 1. System Navigation & Directory Operations

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `pwd` | Prints the absolute path of the current working directory. Essential for verifying current system location before executing destructive commands. | None | Navigation, Basics |
| `cd ~` | Navigates directly to the current user's home directory (`$HOME` or `/root` for root user). | `~` (home directory alias) | Navigation, Path |
| `cd ..` | Moves up exactly one level in the directory hierarchy to the parent directory. | `..` (parent directory reference) | Navigation, Path |
| `cd -` | Toggles back to the previous working directory ($OLDPWD). Extremely useful for switching back and forth between two directories. | `-` (previous working directory) | Navigation, Productivity |
| `cd /var/log` | Navigates to an absolute filesystem path starting from the root directory `/`. | Absolute path starting with `/` | Navigation, Path |
| `mkdir my_project` | Creates a new directory with the specified name in the current working directory. | None | Directory, Filesystem |
| `mkdir -p app/releases/v1/conf` | Creates nested directories in one command. Automatically creates missing parent directories without throwing 'No such file' errors. | `-p` (--parents) | Directory, Automation |

## 2. File Creation & Timestamp Operations

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `touch server.conf` | Creates an empty file if it doesn't exist, or updates access and modification timestamps to the current system time if it already exists. | None | Files, Creation |
| `touch -d "45 days ago" old_backup.tar` | Creates or updates a file with a custom historical timestamp 45 days in the past. Used for testing log rotation, backup retention scripts, and purge cronjobs. | `-d` (custom date string) | Timestamps, Testing |
| `touch -d "30 minutes ago" cache_item.tmp` | Sets the file modification time to exactly 30 minutes in the past. Ideal for testing cache expiration and TTL algorithms. | `-d` (relative time) | Timestamps, Testing |
| `touch -d "1 hour ago" worker.log` | Sets the file timestamp to 1 hour ago. Frequently used to verify hourly log rotation policies. | `-d` (relative time) | Timestamps, Logs |
| `touch -d "50 seconds ago" heartbeat.pid` | Sets the file timestamp to 50 seconds in the past for testing sub-minute timeout detectors and health monitoring daemon alerts. | `-d` (relative time) | Timestamps, Monitoring |
| `touch -d "Jan 1 2025" audit_2025.log` | Sets the modification time to a specific calendar date (Jan 1, 2025 00:00:00) for compliance audit simulations and historical record generation. | `-d` (calendar date string) | Timestamps, Auditing |

## 3. File Listing & Directory Inspection

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `ls -l` | Displays directory contents in long format, showing file permissions, number of hard links, owner, group, file size in bytes, and modification timestamp. | `-l` (long format) | Listing, Inspection |
| `ls -la` | Lists all files in long format, including hidden dotfiles (e.g. `.bashrc`, `.env`, `.ssh/`). Essential for finding hidden configuration files. | `-l` (long), `-a` (all files) | Listing, Hidden Files |
| `ls -lh` | Lists files in long format with human-readable file sizes (K, M, G, T) instead of raw bytes, making capacity assessment instant. | `-l` (long), `-h` (human-readable sizes) | Listing, Disk Space |
| `ls -lt` | Lists directory contents sorted by modification time, displaying the most recently modified files at the top. | `-l` (long), `-t` (sort by time) | Listing, Timestamps |
| `ls -lrt` | Lists directory contents sorted by modification time in reverse order. Newest files appear at the bottom right above your command prompt for effortless visibility. | `-l` (long), `-r` (reverse), `-t` (time) | Listing, Productivity |
| `ls -lRt` | Recursively lists all subdirectories and files sorted by modification time. Provides a complete chronological tree view of the filesystem hierarchy. | `-l` (long), `-R` (recursive), `-t` (time) | Listing, Recursive |

## 4. File Viewing, Paging & Line Numbers

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `cat -n deploy.sh` | Concatenates and prints the complete file content to standard output with continuous line numbering. Great for referencing script lines during pair programming. | `-n` (number all output lines) | Viewing, Line Numbers |
| `tac /var/log/boot.log` | Concatenates and prints files in reverse line order (from bottom to top). Displays the most recent events first without pagination. | Reverse of `cat` | Viewing, Inverted |
| `head -n 25 /var/log/syslog` | Prints the first 25 lines of a specified file. Used to inspect configuration file headers or initial bootstrap logs. | `-n <lines>` (number of lines to show) | Viewing, Header |
| `tail -n 50 /var/log/nginx/access.log` | Prints the last 50 lines of a specified file. Used to inspect recent events or latest application status upon encountering an incident. | `-n <lines>` (number of lines to show) | Viewing, Tail |
| `tail -f /var/log/nginx/error.log` | Follows (-f) appended data in real-time as the file grows. Fundamental tool for live monitoring during deployments or production testing. | `-f` (follow active output stream) | Live Monitoring, Logs |
| `less /var/log/messages` | Opens file in an interactive terminal pager allowing bidirectional scrolling (arrows/PageUp/PageDown), pattern searching (`/pattern`), and low memory overhead on massive files. | `q` to exit, `/` to search forward | Viewing, Interactive Pager |

## 5. Text Processing & Pattern Matching (grep, sed, cut, awk)

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `grep -i 'timeout' /var/log/app.log` | Searches for patterns case-insensitively, catching 'timeout', 'TIMEOUT', 'TimeOut'. | `-i` (ignore case) | Grep, Search |
| `grep -rnw '/var/log/' -e 'ERROR\|FATAL\|CRITICAL'` | Recursively searches directory for exact whole-word occurrences matching multiple patterns using regex OR logic, printing file paths and line numbers. | `-r` (recursive), `-n` (line num), `-w` (word), `-e` (pattern) | Grep, Troubleshooting |
| `grep -v 'DEBUG' application.log` | Inverts matching logic, printing only lines that do NOT contain the specified string. Ideal for stripping noise from log dumps. | `-v` (invert match) | Grep, Filtering |
| `grep -c '502 Bad Gateway' nginx_access.log` | Counts and returns the total number of lines matching the pattern instead of printing the lines. Used for quick metric tallies in bash scripts. | `-c` (count matches) | Grep, Metrics |
| `sed -i.bak 's/PasswordAuthentication yes/PasswordAuthentication no/g' /etc/ssh/sshd_config` | Performs an in-place find-and-replace to harden SSH daemon configuration while preserving a `.bak` backup file for instant rollback. | `-i.bak` (in-place with backup), `s/old/new/g` (global replace) | Sed, Configuration |
| `sed -n '20,40p' /var/log/messages` | Prints specifically lines 20 through 40 of a file, suppressing all other lines. Perfect for extracting exact incident stack traces. | `-n` (suppress default print), `20,40p` (print range) | Sed, Extraction |
| `awk -F: '{if ($3 >= 1000) print $1, $3, $7}' /etc/passwd` | Parses colon-delimited `/etc/passwd` file and prints username ($1), UID ($3), and default shell ($7) for human users (UID >= 1000). | `-F:` (field separator), `$1, $3, $7` (column indexes) | Awk, User Audit |
| `cut -d: -f1,3 /etc/group` | Extracts only the 1st (group name) and 3rd (GID) fields from `/etc/group` using `:` as delimiter. Lightweight alternative to awk for simple CSV/TSV parsing. | `-d:` (delimiter), `-f1,3` (field numbers) | Cut, Text Processing |
| `sort -k2 -n -r metrics.csv \| head -n 10` | Sorts a tabular file numerically (-n) in descending order (-r) based on the 2nd column (-k2), displaying top 10 highest resource consumers. | `-k2` (key column), `-n` (numeric), `-r` (reverse) | Sort, Analytics |
| `uniq -c log_ips.txt \| sort -nr` | Counts consecutive duplicate lines, prepending frequency counts, then sorts by frequency to identify top abusive IP addresses or top errors. | `-c` (count occurrences) | Uniq, Frequency |

## 6. Permissions, Ownership & Sudo Administration

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `chmod 400 jan2026.pem` | Grants read-only permission to the owner, zero permissions to group and others (r--------). Required by SSH clients to prevent 'Permissions are too open' errors. | `4` (read-only for owner), `00` (none for group/others) | Permissions, SSH Keys |
| `chmod 600 ~/.ssh/id_rsa && chmod 700 ~/.ssh` | Restricts SSH private key permissions to read/write for owner only, and directory permissions to read/write/execute for owner only. | `600` (rw-------), `700` (rwx------) | Permissions, Security |
| `chmod 755 /opt/scripts/deploy.sh` | Grants read, write, and execute permissions to owner, and read + execute to group and others (rwxr-xr-x). Standard for executable binary/bash scripts. | `7` (rwx for owner), `5` (r-x for group/others) | Permissions, Scripts |
| `chmod +x entrypoint.sh` | Adds executable permission (+x) to user, group, and others using symbolic mode without modifying existing read or write bits. | `+x` (add execute bit) | Permissions, Scripts |
| `chown -R www-data:www-data /var/www/html` | Recursively changes ownership of all files and folders in web root to user `www-data` and group `www-data`. | `-R` (recursive), `user:group` | Ownership, Web Server |
| `chgrp devops /opt/shared/` | Changes only the group ownership of a directory to `devops` without altering user ownership. | `group` | Ownership, Groups |
| `umask 027` | Sets default permission mask for newly created files (640: rw-r-----) and directories (750: rwxr-x---), preventing access by unprivileged users. | `027` (subtracted from 666 files / 777 dirs) | Security, Umask |
| `usermod -aG docker devops_user` | Appends (-a) user `devops_user` to the `docker` secondary group (-G), allowing non-root Docker socket access without requiring sudo. | `-a` (append), `-G` (supplementary group) | Users, Groups |

## 7. Process Management & System Diagnostics

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `ps aux --sort=-%mem \| head -n 15` | Captures a snapshot of all running processes across all users, sorted by memory percentage in descending order, displaying top 15 memory consumers. | `a` (all users), `u` (user format), `x` (no TTY processes), `--sort=-%mem` | Memory, Process Monitoring |
| `ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu \| head -n 15` | Formatted process listing prioritizing CPU utilization with parent PID identification to diagnose runaway worker threads or zombie processes. | `-eo` (custom output format), `--sort=-%cpu` | CPU, Diagnostics |
| `top -b -n 1 \| head -n 30` | Runs `top` in non-interactive batch mode for exactly one iteration, suitable for logging snapshots into ticket dumps or cron-driven telemetry scripts. | `-b` (batch mode), `-n 1` (single iteration) | Performance, Telemetry |
| `kill -15 <PID>` | Sends graceful SIGTERM signal to process, requesting orderly cleanup of database connections, temp files, and socket releases before exiting. | `-15` (SIGTERM standard termination) | Process, Lifecycle |
| `kill -9 <PID>` | Sends immediate SIGKILL signal to kernel to terminate an unresponsive or hanging process forcefully. Cannot be caught or ignored. | `-9` (SIGKILL forceful termination) | Process, Emergency |
| `pkill -f 'celery worker'` | Matches pattern against full process command lines and sends termination signal to all matching instances across the system. | `-f` (full command line match) | Process, Bulk Kill |
| `systemctl list-units --type=service --state=failed` | Lists all systemd managed services currently in a failed or degraded state across the Linux node. The first diagnostic command to run during node health degradation. | `--type=service`, `--state=failed` | Systemd, Troubleshooting |
| `journalctl -u nginx.service --since "1 hour ago" --no-pager` | Queries systemd journal logs specifically for nginx service over the last hour without piping through a pager, ideal for automated scripts and quick inspections. | `-u <unit>`, `--since <time>`, `--no-pager` | Systemd, Service Debugging |

## 8. Networking, Ports & Remote Access (SSH/SCP/Rsync)

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `ssh -i "jan2026.pem" ec2-user@ec2-15-206-145-107.ap-south-1.compute.amazonaws.com` | Connects securely to a remote AWS EC2 instance using an RSA/Ed25519 identity file (.pem private key) and specified remote user account. | `-i <identity_file>` | SSH, AWS, Remote Access |
| `ss -tulpn` | High-performance modern socket statistics utility displaying all listening TCP/UDP sockets with process IDs (PIDs) and daemon names. | `-t` (tcp), `-u` (udp), `-l` (listening), `-p` (process), `-n` (numeric ports) | Networking, Ports |
| `netstat -tulpn \| grep -E ':(80\|443\|8080\|9000)'` | Displays listening TCP/UDP sockets matching web, proxy, and microservice ports with their owning PIDs. | `-t` (tcp), `-u` (udp), `-l` (listening), `-p` (process), `-n` (numeric) | Networking, Ports |
| `lsof -i :8080` | Identifies which process and user currently hold a lock on port 8080. Essential when application startups fail with 'Address already in use' error. | `-i :<port>` (inspect port binding) | Networking, Troubleshooting |
| `ip a` | Displays all network interfaces, MAC addresses, IPv4/IPv6 CIDR addresses, and link status (UP/DOWN) across the Linux host. | Replaces deprecated `ifconfig` | Networking, IP Address |
| `ip route show default` | Displays the current active default gateway route and corresponding interface (e.g. eth0), crucial for investigating cloud VPC routing drops. | `show default` | Networking, Routing |
| `curl -Iv https://api.service.internal:8443` | Performs a verbose HTTP HEAD request displaying DNS resolution, TLS handshake certificates, cipher negotiation, and response headers. | `-I` (head only), `-v` (verbose diagnostics) | HTTP, TLS, Networking |
| `dig +short mydomain.com @8.8.8.8` | Directly queries Google DNS for A records of a domain bypassing local `/etc/resolv.conf` and systemd-resolved caches to verify external DNS propagation. | `+short` (IP only), `@<dns_server>` | DNS, Troubleshooting |
| `rsync -avzP --exclude '*.log' /src/dir/ user@remote:/dst/dir/` | Synchronizes files incrementally over SSH with archive permissions (-a), compression (-z), progress bar (-P), and exclusions. Highly efficient for migrations. | `-a` (archive), `-v` (verbose), `-z` (compress), `-P` (progress) | Migration, Sync, SSH |

## 9. Disk, Storage & Memory Capacity

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `df -hT --exclude-type=tmpfs --exclude-type=devtmpfs` | Displays human-readable disk filesystem utilization and filesystem types (ext4, xfs) while filtering out in-memory virtual filesystems. | `-h` (human-readable), `-T` (show fstype), `--exclude-type` | Storage, Capacity Planning |
| `du -ah /var/log \| sort -rh \| head -n 20` | Scans `/var/log` recursively, sorts individual files and folders by size in human-readable descending order, and displays top 20 disk space hogs. | `-a` (all files), `-h` (human-readable), `sort -rh` (numeric reverse) | Storage, Troubleshooting |
| `free -m` | Displays total, used, free, shared, buff/cache, and available system RAM and swap space in megabytes. Focus on 'available' for true allocatable memory. | `-m` (display in megabytes) | Memory, Capacity |
| `iostat -xz 1 5` | Reports extended disk I/O metrics every second for 5 iterations, omitting idle devices. Key metrics include `%util` (saturation) and `await` (I/O latency in ms). | `-x` (extended), `-z` (omit inactive), `1 5` (1s interval, 5 counts) | Disk I/O, Performance |
| `vmstat 1 5` | Displays virtual memory, swap activity, I/O wait, system interrupts, and CPU context switches every second. High 'si/so' indicates severe memory pressure. | `1 5` (1s interval, 5 iterations) | Memory, Kernel Diagnostics |
| `lsblk -f` | Lists all block devices (NVMe, EBS, SATA) in a tree diagram showing filesystem types, partition UUIDs, and mount points. | `-f` (show filesystem details) | Storage, Partitions |

## 10. File Searching, Compression & Package Management

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `find /var/log -type f -name "*.log" -mtime +30 -exec gzip {} \;` | Finds all `.log` files in `/var/log` modified more than 30 days ago and compresses them in-place with gzip to reclaim disk capacity. | `-type f` (files), `-name` (glob), `-mtime +30` (>30 days), `-exec` | Disk Management, Automation |
| `find / -type f -size +500M -exec ls -lh {} \;` | Searches entire filesystem for files larger than 500 Megabytes and prints their paths and sizes to resolve 100% disk full emergencies. | `-size +500M` (>500 MB), `-exec ls -lh` | Disk Full, Emergency |
| `tar -czvf backup_$(date +%F).tar.gz /etc/nginx /etc/ssl` | Creates a compressed gzip tarball of Nginx configurations and SSL certificates stamped with current ISO date for configuration backup. | `-c` (create), `-z` (gzip), `-v` (verbose), `-f` (archive filename) | Backup, Archiving |
| `tar -xzvf archive.tar.gz -C /opt/app/` | Extracts a compressed gzip tarball directly into a target directory (`-C /opt/app/`). | `-x` (extract), `-z` (gzip), `-v` (verbose), `-C` (target dir) | Backup, Restore |
| `apt update && apt install -y curl htop jq` | Updates local apt package index from Ubuntu/Debian mirrors and installs common DevOps troubleshooting tools unattended. | `update` (sync repos), `-y` (yes to prompts) | Packages, Debian/Ubuntu |
| `dnf install -y nginx --setopt=install_weak_deps=False` | Installs Nginx on RHEL/CentOS/Amazon Linux 2023 with weak dependencies disabled to maintain a hardened, minimal footprint. | `-y` (unattended), `--setopt` (disable weak deps) | Packages, RHEL/Fedora |
