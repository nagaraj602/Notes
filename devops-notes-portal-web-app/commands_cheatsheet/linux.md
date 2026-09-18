# Linux Commands Cheat Sheet

> Comprehensive Linux administration, system performance diagnostics, networking, and troubleshooting reference with detailed AI explanations.

| Command | Description & AI Explanation | Category / Tags |
| :--- | :--- | :--- |
| `grep -rnw '/var/log/' -e 'ERROR\|FATAL\|CRITICAL'` | Recursively searches through /var/log for lines matching ERROR, FATAL, or CRITICAL, printing line numbers and file paths. Crucial for incident root cause analysis. | Troubleshooting, Logs |
| `awk -F: '{if ($3 >= 1000) print $1, $3, $7}' /etc/passwd` | Parses the system passwd file with ':' delimiter and prints username, UID, and default shell for all regular user accounts (UID >= 1000). Useful for security audits. | Security, User Management |
| `sed -i.bak 's/PasswordAuthentication yes/PasswordAuthentication no/g' /etc/ssh/sshd_config` | Performs an in-place find-and-replace to disable SSH password authentication while preserving a .bak backup file for instant rollback. | Security, SSH, Configuration |
| `find /var/log -type f -name "*.log" -mtime +30 -exec gzip {} \;` | Finds all .log files in /var/log modified more than 30 days ago and compresses them in-place with gzip to reclaim disk capacity. | Disk Management, Maintenance |
| `journalctl -u nginx.service --since "1 hour ago" --no-pager` | Queries systemd journal logs specifically for nginx service over the last hour without piping through a pager, ideal for automated scripts and quick inspections. | Systemd, Service Debugging |
| `systemctl list-units --type=service --state=failed` | Lists all systemd managed services currently in a failed or degraded state across the Linux node. The first diagnostic command to run during node health degradation. | Systemd, Troubleshooting |
| `ps aux --sort=-%mem \| head -n 15` | Snapshot of top 15 memory-consuming processes sorted in descending order, displaying PID, %CPU, %MEM, and complete command line arguments. | Memory, Process Monitoring |
| `ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu \| head -n 15` | Formatted process listing prioritizing CPU utilization with parent PID identification to diagnose runaway worker or zombie processes. | CPU, Performance Diagnostics |
| `top -b -n 1 \| head -n 30` | Runs top in non-interactive batch mode for exactly one iteration, suitable for logging snapshots into ticket dumps or cron-driven telemetry scripts. | CPU, Performance Diagnostics |
| `netstat -tulpn \| grep -E ':(80\|443\|8080\|9000)'` | Displays listening TCP/UDP sockets with process IDs and program names matching common web and microservice ports. | Networking, Ports |
| `ss -tulpn` | Modern, high-performance socket statistics replacement for netstat, directly parsing kernel socket tables to list all active listening daemon sockets. | Networking, Performance |
| `lsof -i :8080` | Identifies which process and user currently hold a lock on port 8080. Essential when application startups fail with 'Address already in use' error. | Networking, Troubleshooting |
| `ip route show default` | Displays the current active default gateway route and corresponding interface (e.g. eth0), crucial for investigating cloud VPC routing drops. | Networking, Routing |
| `df -hT --exclude-type=tmpfs --exclude-type=devtmpfs` | Displays human-readable disk filesystem utilization and filesystem types (ext4, xfs) while filtering out in-memory virtual filesystems. | Storage, Capacity Planning |
| `du -ah /var/log \| sort -rh \| head -n 20` | Scans /var/log recursively, sorts individual files and folders by size in human-readable descending order, and displays top 20 disk space hogs. | Storage, Troubleshooting |
| `iostat -xz 1 5` | Reports extended disk I/O metrics every second for 5 iterations, omitting idle devices. Key metrics include %util (saturation) and await (I/O latency in ms). | Disk I/O, Performance |
| `vmstat 1 10` | Displays virtual memory, swap activity, I/O wait, system interrupts, and CPU context switches every second. High 'si/so' indicates severe memory pressure and swap thrashing. | Memory, Kernel Diagnostics |
| `chmod 600 ~/.ssh/id_rsa && chmod 700 ~/.ssh` | Restricts SSH private key permissions to read/write by owner only, and directory permissions to read/write/execute by owner only. Prevents SSH client refusal errors. | Security, Permissions |
| `chown -R www-data:www-data /var/www/html` | Recursively changes ownership of web root files to the www-data web server user and group, ensuring web application file upload permissions. | Permissions, Web Server |
| `tar -czvf backup_$(date +%F).tar.gz /etc/nginx /etc/ssl` | Creates a compressed gzip tarball of Nginx configurations and SSL certificates stamped with current ISO date for configuration backup. | Backup, Archiving |
| `rsync -avzP --exclude '*.log' /src/dir/ user@remote:/dst/dir/` | Synchronizes files incrementally over SSH with archive permissions (-a), compression (-z), progress bar (-P), and exclusions. Highly efficient for cloud server migrations. | Migration, Sync, Networking |
| `strace -p <PID> -f -e trace=network,file` | Attaches to a running process ID and tracks all network and file-related system calls in real-time. Unmatched for diagnosing hanging processes or missing configs. | Kernel, Deep Troubleshooting |
| `curl -Iv https://api.service.internal:8443` | Performs a verbose HTTP HEAD request displaying DNS resolution, TLS handshake certificates, cipher negotiation, and response headers. | HTTP, TLS, Networking |
| `dig +short mydomain.com @8.8.8.8` | Directly queries Google DNS for A records of a domain bypassing local /etc/resolv.conf and systemd-resolved caches to verify external DNS propagation. | DNS, Networking |
| `tcpdump -i eth0 -nn 'tcp port 443 and (tcp-syn != 0)'` | Captures only initial TCP SYN packets arriving on port 443 of eth0 interface, pinpointing new inbound connection requests and dropped handshakes. | Packet Analysis, Security |
