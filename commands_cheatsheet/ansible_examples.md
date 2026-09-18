# Ansible Example Playbooks

> Production Ansible playbooks for Nginx web server deployment, security hardening, and rolling service restarts.

## 1. Production Nginx Reverse Proxy with SSL Hardening Playbook
**Description**: Installs Nginx, generates DH parameters, copies hardened TLS configuration, and enables systemd service.

```yaml
---
- name: Deploy and Harden Nginx Reverse Proxy
  hosts: webservers
  become: yes
  vars:
    app_port: 8080
    server_domain: "api.mycompany.com"
  
  tasks:
    - name: Ensure Nginx is installed
      apt:
        name: nginx
        state: present
        update_cache: yes

    - name: Deploy hardened Nginx site configuration
      template:
        src: templates/nginx_reverse_proxy.j2
        dest: "/etc/nginx/sites-available/{{ server_domain }}"
        owner: root
        group: root
        mode: '0644'
      notify: Reload Nginx

    - name: Enable site configuration
      file:
        src: "/etc/nginx/sites-available/{{ server_domain }}"
        dest: "/etc/nginx/sites-enabled/{{ server_domain }}"
        state: link

    - name: Ensure default site is disabled
      file:
        path: /etc/nginx/sites-enabled/default
        state: absent
      notify: Reload Nginx

  handlers:
    - name: Reload Nginx
      systemd:
        name: nginx
        state: reloaded
```

## 2. Zero-Downtime Rolling Service Restart Playbook
**Description**: Executes rolling restarts across clustered application servers one host at a time (serial: 1), validating health before advancing.

```yaml
---
- name: Zero-Downtime Rolling Service Restart
  hosts: app_cluster
  serial: 1
  become: yes

  tasks:
    - name: Remove host from load balancer pool
      command: /usr/local/bin/alb-deregister-instance.sh "{{ inventory_hostname }}"
      delegate_to: localhost

    - name: Restart application daemon
      systemd:
        name: my-backend-service
        state: restarted

    - name: Wait for internal health check endpoint
      uri:
        url: "http://{{ ansible_default_ipv4.address }}:8080/health"
        status_code: 200
      register: health_result
      until: health_result.status == 200
      retries: 12
      delay: 5

    - name: Re-register host back to load balancer pool
      command: /usr/local/bin/alb-register-instance.sh "{{ inventory_hostname }}"
      delegate_to: localhost
```
