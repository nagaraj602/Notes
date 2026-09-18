# Ansible Commands Cheat Sheet

> Essential Ansible ad-hoc commands, playbook executions, inventory queries, and vault encryption operations.

| Command | Description & AI Explanation | Category / Tags |
| :--- | :--- | :--- |
| `ansible all -i inventory.ini -m ping` | Executes the ping module across all inventory hosts to verify SSH connectivity, Python interpreter availability, and authentication. | Ad-Hoc, Connectivity |
| `ansible webservers -i inventory.ini -m command -a "uptime"` | Runs arbitrary shell command 'uptime' across all nodes grouped under [webservers] without spawning a sub-shell. | Ad-Hoc, Operations |
| `ansible-playbook -i inventory.ini site.yml --syntax-check` | Validates playbook YAML syntax, task structure, and jinja2 templating errors without connecting to remote nodes. | Linting, Quality Gate |
| `ansible-playbook -i inventory.ini site.yml --check --diff` | Runs in dry-run simulation mode (--check) and prints unified diffs (--diff) of file and configuration changes that would occur. | Dry-run, Safe Execution |
| `ansible-playbook -i inventory.ini deploy.yml --tags "nginx,ssl" --skip-tags "backup"` | Executes only tasks tagged with 'nginx' or 'ssl', skipping long-running backup tasks for accelerated hotfix deployments. | Selective Execution |
| `ansible-playbook -i inventory.ini deploy.yml --limit "web-node-01"` | Limits execution of the entire playbook strictly to host 'web-node-01', useful for canary testing changes on a single server. | Canary, Scoping |
| `ansible-vault encrypt secrets.yml --vault-password-file .vault_pass` | Encrypts sensitive variables file with AES-256 cipher using password from local file, allowing secure storage in Git repositories. | Security, Vault |
| `ansible-vault view secrets.yml` | Decrypts and displays the contents of an encrypted vault file in the terminal pager without saving plain text to disk. | Vault, Inspection |
| `ansible-vault edit secrets.yml` | Opens encrypted vault file in default text editor, decrypting in memory and re-encrypting upon saving and exiting. | Vault, Maintenance |
| `ansible-galaxy install -r requirements.yml -p ./roles` | Downloads and installs community or internal reusable roles specified in requirements.yml from Ansible Galaxy or private Git repos. | Roles, Dependencies |
| `ansible-inventory -i inventory.ini --graph` | Renders visual hierarchical tree of inventory host groups and nested child groups for clear topology visualization. | Inventory, Discovery |
