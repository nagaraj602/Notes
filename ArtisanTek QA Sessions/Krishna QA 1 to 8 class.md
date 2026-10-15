# **QA by Krishna 11-Feb-2026 18-06-08**

## **1\. SSH & Passwordless Authentication Between Linux Servers**

### **Questions & Sub-Questions Asked:**

1. **Primary Question:** How can we establish a passwordless SSH connection between two Linux servers? Can you provide an architectural overview rather than just commands or screenshots?  
   * *Sub-Question:* If you are in an interview and asked how to set up passwordless SSH, how would you articulate the process step by step?  
   * *Sub-Question:* Given Server A (source) and Server B (target), what exact sequential steps are required to establish a connection from Server A to Server B?  
   * *Sub-Question:* How do you generate a key pair in Linux?  
   * *Sub-Question:* What is the output of the key generation command (ssh-keygen \-t rsa), and what are the generated files called?  
   * *Sub-Question:* Once the key pair is generated, what is the next step?  
   * *Sub-Question:* Which key file gets copied, into which specific file, and on which server (Server A or Server B)?

### **Technical Guidance & Instructor Solution:**

* **Interview-Ready Process:**  
  1. **Generate Key Pair (on Server A):** Execute ssh-keygen \-t rsa. This generates an asymmetric key pair inside the \~/.ssh/ directory:  
     * id\_rsa (Private Key – strictly confidential, never shared or copied).  
     * id\_rsa.pub (Public Key).  
  2. **Transfer Public Key:** Copy the contents of the public key (id\_rsa.pub) from Server A to Server B.  
  3. **Authorize Key (on Server B):** Append the public key string into Server B's \~/.ssh/authorized\_keys file.  
  4. **Authenticate:** Connect from Server A using ssh \<user\>@\<server\_b\_ip\> without password authentication.  
* **Correction:** Never attempt to copy the private key to a remote server's authorized\_keys file. The private key must stay secure on the client machine.

## **2\. Linux User Management & Sudo Privileges**

### **Questions & Sub-Questions Asked:**

1. **Primary Question:** How do you create a new user in Linux?  
2. **Primary Question:** How do you grant sudo privileges to a newly created user?  
3. **Primary Question:** What are sudo privileges, and how are they useful in administrative operations?  
   * *Sub-Question:* What is the fundamental definition of sudo?

### **Technical Guidance & Instructor Solution:**

* **User Creation & Sudo Assignment:**  
  * Create the user via useradd \<username\> (or sudo adduser \<username\>).  
  * Grant privileges by adding the user to the sudo group (Debian/Ubuntu: usermod \-aG sudo \<username\>) or the wheel group (RHEL/CentOS: usermod \-aG wheel \<username\>), or by configuring an entry in /etc/sudoers via visudo.  
* **Technical Definition of Sudo:**  
  * **Sudo (SuperUser DO):** A mechanism that allows an authorized non-root user to execute administrative tasks with root-level privileges while maintaining an audit trail and preventing unauthorized full-root login access.

## **3\. Package Management & Network Utilities**

### **Questions & Sub-Questions Asked:**

1. **Primary Question:** What is yum?  
   * *Sub-Question:* Technically, what category of tool is yum called (e.g., packages vs. package manager)?  
2. **Primary Question:** What is the wget command used for?

### **Technical Guidance & Instructor Solution:**

* **Package Management (yum):**  
  * yum (Yellowdog Updater, Modified) is an automated **package manager** for RPM-based distributions (such as RHEL/CentOS) used to search, install, update, and resolve dependencies for software packages (analogous to apt on Debian/Ubuntu).  
* **Network Utility (wget):**  
  * A non-interactive command-line tool used to retrieve and download files and archives directly from web servers using protocols like HTTP, HTTPS, and FTP.

## **4\. File Permissions & Directory Modes**

### **Questions & Sub-Questions Asked:**

1. **Primary Question:** What does chmod 775 mean for a file or directory?  
   * *Sub-Question:* What does the numeric value 7 specifically stand for?  
   * *Sub-Question:* Do files or folders have 777 permissions by default?

### **Technical Guidance & Instructor Solution:**

* **Permission Breakdown:**  
  * The digit 7 represents full permissions: Read ($4$) \+ Write ($2$) \+ Execute ($1$) $=7$ (rwx).  
  * chmod 775 assigns:  
    * **Owner (User):** 7 (rwx – Read, Write, Execute)  
    * **Group:** 7 (rwx – Read, Write, Execute)  
    * **Others:** 5 (r-x – Read, Execute)  
* **Default Directory Permissions:**  
  * Folders do **not** default to 777. Default permissions are governed by the system's umask (typically default directory permissions are 755 and files are 644).

## **5\. Linux Text Processing & File Searching (grep, find, cut, awk)**

### **Questions & Sub-Questions Asked:**

1. **Primary Question:** How can you search for a specific keyword inside a file or across an entire folder?  
   * *Sub-Question:* Suppose there are 10 files in a directory and the file name is unknown. How can you identify which file contains the target keyword?  
   * *Sub-Question:* What is the complete command syntax for this operation using grep?  
2. **Primary Question:** How can you find all files that were modified within the last 10 days?  
3. **Primary Question:** How can you search for files whose size is less than 100 MB or less than 10 MB?  
4. **Primary Question:** What is the difference between the cut command and the awk command?

### **Technical Guidance & Instructor Solution:**

* **Recursive Keyword Search (grep):**  
  * Do not provide single-word answers. Explain the utility and its flags:  
  * Bash

grep \-rn "keyword" /path/to/directory/

*   
  * \-r / \-R: Recursively inspects all subdirectories and files.  
    * \-n: Displays the matched line number.  
    * \-l *(optional)*: Outputs only the matching file names when the contents are not needed.  
* **Locating Files by Modification Time (find):**  
  * Use the find utility with the \-mtime parameter:  
  * Bash

find /path/to/search \-type f \-mtime \-10

*   
  * \-mtime \-10: Matches files modified less than 10 days ago.  
* **Locating Files by Size:**  
  * Use the find utility with the \-size filter:  
  * Bash

find /path/to/search \-type f \-size \-10M  
find /path/to/search \-type f \-size \-100M

*   
  * \-size \-10M: Matches regular files with a size strictly under 10 megabytes.  
* **cut vs. awk:**  
  * **cut:** A simple column/delimiter-based stream filter designed for basic field extraction where lines are separated by a consistent single-character delimiter (e.g., cut \-d: \-f1).  
  * **awk:** A comprehensive, Turing-complete text-processing programming language capable of parsing complex and varying whitespace, running conditional statements, performing arithmetic calculations, and formatting output data.

## **6\. Apache Tomcat Deployment & Troubleshooting**

### **Questions & Sub-Questions Asked:**

1. **Primary Question:** Can you summarize the end-to-end setup process for installing and configuring Apache Tomcat (overview of architecture/steps, without reading command-by-command)?  
2. **Primary Question:** Which Linux distribution/server environment are you using for the installation?  
3. **Primary Question:** When a server crashes or becomes unresponsive during deployment, how do you troubleshoot it?  
   * *Sub-Question:* Did you attempt to connect to the instance to diagnose the root cause, and what tool was used to attempt access?

### **Technical Guidance & Instructor Solution:**

* **Tomcat Deployment Lifecycle:**  
  * Install prerequisite Java runtime (OpenJDK).  
  * Create a dedicated system user/group for Tomcat (security isolation).  
  * Download the binary archive via wget and extract to /opt/.  
  * Configure ownership and file permissions.  
  * Configure systemd service unit file (tomcat.service) for lifecycle management (startup.sh / shutdown.sh).  
  * Update inbound network firewall/AWS Security Group rules (e.g., port 8080 or custom port).  
  * Configure tomcat-users.xml and comment out IP restriction valves in context.xml to allow remote GUI access to Manager and Host Manager apps.  
* **Platform Recommendation & Diagnostics:**  
  * If Ubuntu environments fail repeatedly under heavy service configurations, migrate to Red Hat Enterprise Linux (RHEL) for standard enterprise stability.  
  * Rebooting an EC2 instance via the AWS console is insufficient; inspect system logs (journalctl \-u tomcat, /var/log/messages, /var/log/syslog, or Tomcat's catalina.out) via SSH/PuTTY to address the underlying root cause.

## **7\. Assignment Protocols & Professional Communication Standards**

### **Questions Asked:**

1. "Have you completed the assignment or not?"  
2. "Will you be able to do this hands-on right now if asked to demonstrate?"  
3. "Where are the step-by-step screenshots?"  
4. "Is this the entire assignment?"  
5. "Where are you encountering upload issues with the Google Drive repository?"

### **Standards Established by the Instructor:**

* **Documentation & Submission Workflow:**  
  * Every step of an assignment must have visual verification (terminal screenshots).  
  * Screenshots must be compiled into a single consolidated PDF document.  
  * The PDF must be reviewed and approved by the instructor during QA before being uploaded to Google Drive.  
* **Interview Delivery Expectations:**  
  * Avoid conversational, casual language (e.g., "ABCD language").  
  * Do not give terse one-word answers or line-by-line code recitations.  
  * Structure answers logically: state the technical definition, detail the 3–4 high-level steps, and use standard DevOps industry terminology.

# 2\. QA by Krishna 13-Feb-2026 20\_01\_01 

### **1\. General Session & Technical Communication Standards**

* **Questions Asked:**  
  * Can you hear me?  
  * Have you completed and submitted the assigned tasks/assessments on time?  
  * What have you practiced from what was taught in class?  
* **Instructor Guidance & Recommendations:**  
  * **Interview-Ready Communication:** Avoid casual phrasing (such as *"copying the data/text"*). Use industry-standard technical terminology (e.g., *key pair*, *public key*, *private key*, *authorized\_keys*).  
  * **Structured Delivery:** Do not provide one-line, vague answers. Structure explanations step-by-step (Step 1, Step 2, Step 3\) rather than bundling or overcomplicating with irrelevant context (e.g., explaining instance creation when asked about network connectivity).  
  * **Precision:** Listen to the exact scope of the question before executing commands; do not rush into arbitrary configurations.

### **2\. SSH & Passwordless Authentication**

* **Main Questions:**  
  * How do you explain the process of establishing a passwordless connection between two servers?  
  * If assigned the task to establish a passwordless connection between Server A and Server B, what is the step-by-step process?  
    1. What is the first step?  
    2. What is the second step?  
    3. What is the third step?  
  * What is the complete command used to generate a key pair using `ssh-keygen`?  
  * What specific files/outputs are generated when running the key generation command?  
  * Where is the generated key pair stored on the server?  
  * If you cannot find the `.ssh` folder, how do you locate or handle it?  
  * Can you demonstrate establishing a passwordless connection between two instances in real-time?  
    1. What steps must be executed on the source instance?  
    2. What steps must be executed on the destination instance?  
* **Instructor Guidance & Provided Model Answer:**  
  * **Definition of a Key Pair:** A key pair is not two separate pairs; it is a single pair consisting of one public key and one private key.  
  * **Step-by-Step Procedure:**  
    1. **Step 1 (Generate Key Pair):** Run `ssh-keygen -t rsa` on the source server. This creates two keys in the `.ssh` directory: the private key (`id_rsa`) and the public key (`id_rsa.pub`).  
    2. **Step 2 (Copy Public Key):** Copy the contents of the public key (`id_rsa.pub`) into the `authorized_keys` file located inside the `.ssh` directory of the target/destination server.  
    3. **Step 3 (Initiate Connection):** Connect from Server A to Server B using `ssh <user>@<IP_Address>`.

### **3\. Linux File Permissions & Default Mask (`umask`)**

* **Main Questions:**  
  * Can you create a file and identify its current permissions?  
    * What are the specific permissions assigned to the newly created file?  
    * What type of access does the user (owner), group, and others possess?  
    * How do you read permission notations (e.g., what does `rw-r--r--` represent)?  
    * If default file permissions are `666`, why does the created file show `rw-r--r--`?  
  * How do you modify existing permissions of a file?  
    * How do you grant write permission to "others" without altering owner/group access?  
    * How do you verify and confirm that the permission has updated in the system output?  
  * How do you configure permissions at file creation time rather than modifying them after?  
    * How can the default creation permission be set to `rwxrw-rw-` at the moment a file is created?  
    * What is `umask`?  
    * How is the `umask` calculated/computed against default system file permissions?  
    * What is the default value of `umask`, and what mathematical change must be applied to achieve the target permissions?

### **4\. User Administration & Privileges**

* **Main Questions:**  
  * Can you demonstrate how to create a new user in Linux?  
  * How do you grant `sudo` (administrative/root) permissions to the newly created user?

### **5\. File Management, Archiving & Log Analysis**

* **Main Questions:**  
  * How do you search for and locate all files across the server having a `.log` extension?  
  * How do you list files in the current working directory?  
  * How do you create multiple files simultaneously (e.g., `F1`, `F2`, `F3`)?  
  * How do you archive and compress multiple files into a single zip file?  
  * Where are system log files located by default, and how do you navigate to that directory?  
    * How do you view the directory contents and inspect specific log files (such as `cloud-init.log`)?  
  * How do you filter and extract specific entries (e.g., searching strictly for the keyword `error`) within a log file?  
    * How is the search command executed across different keywords or log files?  
* **Instructor Guidance Provided:**  
  * **Log Directory Path:** The standard directory path for system logs is `/var/log` (`cd /var/log`).

### **6\. Session Wrap-Up & Operational Logistics**

* **Questions Asked:**  
  * Did I miss anyone?  
  * Does anyone have questions?  
* **Instructor Answers Provided to Student Queries:**  
  * **Assignment Submission Process:** Students should compile their work along with verification screenshots into a single PDF document and upload it.  
  * **Class Schedule:** QA sessions are scheduled within the window of **5:30 PM to 8:30 PM**. Notices are shared at least 1 hour prior based on instructor availability. If no live QA is conducted on a given day, students are expected to utilize that time block for self-practice.

# 3\. QA by Krishna 14-Feb-2026 17\_46\_20

### **1\. General & Course Progress**

* **Question:** What are the topics covered in Shell Scripting / Linux until now?  
* **Sub-Question:** What is value?  
* **Instructor's Answer / Suggestion:** *None provided.*

### **2\. Text Processing (`cut` & `awk`)**

* **Question:** What is the difference between the `cut` and `awk` commands?  
* **Sub-Questions:**  
  * What is that field separator called?  
  * What is a delimiter?  
* **Instructor's Answer / Suggestion:** *None provided.*

### **3\. Memory & Process Management**

* **Question:** What is swap space?  
* **Instructor's Answer / Suggestion:** *None provided.*  
* **Question:** What is a zombie process?  
* **Instructor's Answer / Suggestion:** Note it down, research it, learn it, and come back prepared for the next QA session.

### **4\. Storage Management (LVM)**

* **Question:** What is LVM (Logical Volume Manager)?  
* **Instructor's Answer / Suggestion:** When encountering a new concept for the first time, write it down and prepare it for subsequent sessions.

### **5\. Networking Basics & Monitoring**

* **Question:** Can you give any five networking commands that are useful in your day-to-day work?  
* **Instructor's Answer / Suggestion:** *None provided.*  
* **Question:** How do you check the kernel version on your server?  
* **Sub-Question:** What do you name / what is the `uname` command?  
* **Instructor's Answer / Suggestion:** *None provided.*  
* **Question:** What is the purpose of the `netstat` command?  
* **Sub-Questions:**  
  * Overall, what is the purpose of `netstat`?  
  * What is `ps -ef` / process checking used for?  
* **Instructor's Answer / Suggestion:**  
  * `netstat` is used to troubleshoot network issues, check listening ports, verify open ports, and resolve port-related problems.  
  * Answer interview questions with confidence and clarity rather than hesitation.

### **6\. File System Links**

* **Question:** What is the difference between a soft link and a hard link?  
* **Instructor's Answer / Suggestion:** *None provided.*  
* **Question:** What is an inode value?  
* **Sub-Question:** What does unique identification mean in detail (beyond a one-word or one-line definition)?  
* **Instructor's Answer / Suggestion:** *None provided.*

### **7\. File Operations (`find` & `mv`)**

* **Question:** How can we find empty files on your server?  
* **Sub-Questions:**  
  * Can you repeat the command?  
  * Can you write the command in the chat?  
  * Is the command correct without specifying the filename?  
* **Instructor's Answer / Suggestion:** Confirmed the student's reasoning (`find` command for empty files without naming a specific file).  
* **Question:** How do we rename a file?  
* **Instructor's Answer / Suggestion:** *None provided.*

### **8\. Network Protocols & Default Ports**

* **Question:** What is the default port for SSH?  
* **Sub-Questions:**  
  * What about Tomcat?  
  * What about Jenkins? *(Instructor noted: Port 80 is incorrect)*  
  * What about HTTPS? *(Instructor noted: Port 6443 is incorrect)*  
  * What is the RDP port number?  
* **Instructor's Answer / Suggestion:**  
  * Common day-to-day service ports must be memorized and ready at your fingertips: Telnet, SSH, Jenkins, Tomcat, HTTP, HTTPS, and RDP.

### **9\. Remote Access: Telnet vs. SSH**

* **Question:** What is the difference between Telnet and SSH?  
* **Sub-Questions:**  
  * Which port does SSH run on?  
  * Which port does Telnet run on?  
  * When and why do we use Telnet? If it is not secure, what is the purpose of that command?  
* **Instructor's Answer / Suggestion:**  
  * Telnet runs on port 23 (correcting the student's answer of 21).  
  * SSH is secure, whereas Telnet is unsecure.  
  * Linux fundamentals are mandatory prerequisites for higher-level DevOps tools (like Jenkins), as server-level troubleshooting relies heavily on strong foundational knowledge.

### **10\. Process Monitoring**

* **Question:** How do you check running processes or running services on a Linux server?  
* **Instructor's Answer / Suggestion:** *None provided.*

### **11\. Disk Usage & Partition Monitoring (`df` vs. `du`)**

* **Question:** How do you check disk space on a Linux server?  
* **Sub-Questions:**  
  * What is the complete command used to check available disk space?  
  * If asked for the disk space utilization on your server, what is your answer and next step?  
  * What does `df -h` show when executed?  
  * When running `df`, it displays multiple partitions—what does that mean?  
  * What is the difference between `du` and `df`?  
  * Why do we use `du`?  
* **Instructor's Answer / Suggestion:**  
  * Basic Linux commands like `df -h` and `du -h` must be thoroughly prepared before progressing from basic to intermediate and advanced levels.

### **12\. Memory Utilization**

* **Question:** How do you check RAM on your server?  
* **Instructor's Answer / Suggestion:** *None provided (instructed student to review and prepare).*

### **13\. Text Replacement & Stream Editing (`sed`)**

* **Question:** Given a file with content, how do you find a specific keyword and replace it with another (e.g., replacing every occurrence of "Kumar" with "Krishna")?  
* **Sub-Questions:**  
  * What is the exact command/line using the stream editor (`sed`)?  
  * Can you explain how the command works?  
* **Instructor's Answer / Suggestion:** *None provided.*

# 4\. QA by Krishna \[17-Feb-2026 17\_28\_48

#### **1\. Difference between Soft Link and Hard Link**

* **Question:** Can you explain the difference between a soft link and a hard link?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **2\. Process and System Monitoring (`top` vs. `htop`)**

* **Question:** What is the difference between `top` and `htop`?  
  * **Sub-question:** If `ps` checks running processes and commands like `free` check memory, why should `top` be used?  
  * **Sub-question:** What detailed information does `top` provide?  
  * **Sub-question:** Can process IDs not already be viewed using `ps -ef`?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **3\. Zombie Processes**

* **Question:** What is a zombie process?  
  * **Sub-question:** Can you explain it step by step?  
  * **Sub-question:** How do you identify/check zombie processes?  
  * **Sub-question:** How do you check processes in general?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **4\. Disk Space Commands (`du` vs. `df`)**

* **Question:** How do you check disk space?  
  * **Sub-question:** What output does `df -h` provide?  
  * **Sub-question:** What is the difference between `du` and `df`?  
  * **Sub-question:** When asked to check disk space, why choose `du`?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **5\. Disk Space Verification**

* **Question:** What is the difference between `du` and `df`?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **6\. Process Termination Signals**

* **Question:** What is the difference between `kill` and `kill -9`?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **7\. Load Average Interpretation**

* **Question:** What is load average?  
  * **Sub-question:** How do you read it?  
  * **Scenario-based Sub-question:** If the load average values are `1.2`, `0.9`, and `0.7`, what do they mean?  
  * **Sub-question:** What is the purpose of the three different values?  
  * **Sub-question:** How do the 1-minute, 5-minute, and 15-minute values indicate whether the server load is increasing or decreasing?  
  * **Sub-question:** How can the overall system load output be summarized from the load average?  
* **Instructor's Answer / Suggestion:**  
  * Load average values correspond to 1-minute, 5-minute, and 15-minute intervals.  
  * They are used to observe server load trends and determine whether system utilization is actively increasing or decreasing over time.

#### **8\. Service Management**

* **Question:** How do you check whether services are running or not on your server?  
  * **Sub-question:** What is the exact command using `status` and the service name?  
  * **Sub-question:** What is the difference between using the `service` command (e.g., `sudo service tomcat status/start/stop`) and using `systemctl`?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **9\. Network Port Inspection**

* **Question:** How do you check which ports are listening on your server?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **10\. Shell Redirection Operators**

* **Question:** What is the difference between append (`>>`) and redirect (`>`)?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **11\. Shebang Line**

* **Question:** What is a shebang?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **12\. Remote File Transfer**

* **Question:** What is the difference between `scp` and `rsync`?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **13\. Linux Architecture**

* **Question:** Can you explain the Linux architecture?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **14\. System Performance Monitoring**

* **Question:** How do you monitor system performance?  
  * **Sub-question:** Are `top` and `htop` the only two commands used?  
  * **Sub-question:** What all do you monitor when checking system performance?  
  * **Sub-question:** What specific metrics do you check with `ps`, `htop`, `top`, and `free`?  
* **Instructor's Answer / Suggestion:**  
  * When addressing system performance in an interview, address all resource aspects thoroughly (CPU, memory, disk, processes) rather than providing brief one-word or one-line answers. Reserve single-command answers for questions targeted strictly at one component (such as memory or disk space alone).

#### **15\. Zombie Process Details**

* **Question:** What is a zombie process?  
  * **Sub-question:** Can you provide an example of what a zombie process looks like?  
  * **Sub-question:** How can a zombie process be found/identified?  
  * **Sub-question:** Can you explain the concept of a zombie process in detail before discussing the command?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **16\. Special File Permissions (Sticky Bit)**

* **Question:** What is a sticky bit?  
  * **Sub-question:** Since `chmod` is already used to assign directory permissions, how does a sticky bit secure directories against unauthorized users?  
  * **Sub-question:** Why is a sticky bit required, and what is its specific purpose on a directory?  
* **Instructor's Answer / Suggestion:**  
  * A sticky bit is a special permission applied to a shared directory that prevents users from deleting files created by other users.

#### **17\. User Privilege Escalation (`su` vs. `sudo`)**

* **Question:** What is the difference between `su` and `sudo`?  
  * **Sub-question:** Does `sudo` not ask for a password?  
* **Instructor's Answer / Suggestion:**  
  * `su` stands for "switch user" and is used to switch between user accounts.  
  * `sudo` is used to execute commands with root/superuser privileges.

#### **18\. Permission Octal Codes**

* **Question:** What does `chmod 755` do?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **19\. Group Management**

* **Question:** How can we change the group for a particular folder or file?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **20\. Ownership Management (`chown`)**

* **Question:** What is `chown` used for?  
  * **Sub-question:** What is the syntax for the `chown` command?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **21\. Curriculum Check**

* **Question:** What topics have been covered in shell scripting so far?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **22\. Practical Shell Scripting**

* **Question:** Are you able to write a shell script on screen?  
  * **Task:** Write a script for the addition of two numbers.  
  * **Follow-up Sub-question:** If values should not be hardcoded in the script (e.g., `num1=2`, `num2=2`), how should dynamic values be provided?  
* **Instructor's Answer / Suggestion:**  
  * Dynamic values should be passed as command-line arguments (e.g., `$1`, `$2`).  
  * *Additional Feedback:* Use precise technical terminology when explaining solutions rather than informal or casual descriptions.

#### **23\. File Transfer and Synchronization**

* **Question:** Can you explain the difference between `scp` and `rsync`?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **24\. SSH Configuration**

* **Question:** How can we establish a passwordless connection between two servers?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **25\. Remote Access Protocols (SSH vs. Telnet)**

* **Question:** What is the difference between SSH and Telnet?  
  * **Sub-question:** Where is Telnet used in real-world scenarios if it is rarely used for remote access?  
* **Instructor's Answer / Suggestion:**  
  * Telnet is primarily used for network troubleshooting purposes.

#### **26\. Text Processing Tools (`awk` vs. `cut`)**

* **Question:** Can you explain the difference between `awk` and `cut`?  
  * **Sub-question:** Is column-wise versus row-and-column processing the only difference?  
  * **Sub-question:** How is a delimiter specified and used in `cut` versus `awk`?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **27\. Pattern Searching**

* **Question:** How can we find a specific keyword in a file (for example, finding error occurrences in a syslog file)?  
* **Instructor's Answer / Suggestion:** *None provided in the transcript.*

#### **28\. Server Performance Troubleshooting**

* **Question:** If a Linux server is responding very slowly, how do you troubleshoot the issue?  
* **Instructor's Answer / Suggestion:**  
  * **Step 1 (Identify):** Use monitoring utilities such as `top` or primarily `htop` to identify the core bottleneck.  
  * **Step 2 (Analyze Metrics):** Review resource utilization across processes: evaluate CPU load, memory consumption, and available swap memory to determine whether the server is sustaining the current load.  
  * **Step 3 (Isolate & Debug):** If high CPU utilization is detected, identify the specific process consuming excessive CPU, investigate the root cause of the spike, and proceed with targeted debugging.

# 5\. QA by Krishna 20-Feb-2026 20\_19\_19\_25

### **1\. Practical Shell Scripting: Addition of Two Numbers**

* **Question:** What is the status of the script?  
* **Sub-Question:** If you are taking this much time to resolve the issue for a basic addition of two numbers, what have you prepared?  
* **Sub-Question:** Did you read the error?  
* **Sub-Question:** Shouldn't we rerun it? Why are you doing that?  
* **Sub-Question:** It is still showing the same error; why is it showing?  
  * **Instructor's Suggestion / Feedback:**  
    * Please prepare thoroughly and practice practically before attending. A simple shell script for adding two numbers should not take this much time.

### **2\. Shell Scripting: Special Variables & File Operators**

* **Question:** Can you explain special variables in shell scripting?  
  * **Instructor's Suggestion / Answer:** *(No answer provided by instructor)*  
* **Question:** What are file operators?  
* **Sub-Question:** Can you explain all the file operators?  
* **Sub-Question:** Can you list and explain all file operators beyond just `-f`, `-r`, `-w`, and `-x`?  
  * **Instructor's Suggestion / Feedback:**  
    * There are more file operators than just the basic read, write, and execute permissions; go through and learn all of them.

### **3\. Networking: Telnet & SSH**

* **Question:** What is Telnet used for? What is the purpose of it?  
  * **Instructor's Suggestion / Answer:** *(No answer provided by instructor)*  
* **Question:** What is the difference between Telnet and SSH?  
* **Sub-Question:** What do you mean by "production" in this context?  
  * **Instructor's Answer:**  
    * SSH is used to connect between servers securely. Telnet is not secure.

### **4\. Linux Commands: Disk Space & Package Managers**

* **Question:** How do you check disk space in Linux?  
* **Sub-Question:** What is the difference between `df -h` and `du -h`?  
  * **Instructor's Suggestion / Answer:** *(No answer provided by instructor)*  
* **Question:** What is the default port for Jenkins?  
* **Sub-Question:** What is the default port for HTTPS?  
  * **Instructor's Suggestion / Answer:** *(No answer provided by instructor)*  
* **Question:** What is the package manager for CentOS?  
* **Sub-Question:** What is the package manager for Ubuntu?  
  * **Instructor's Suggestion / Answer:** *(No answer provided by instructor)*

### **5\. Practical Shell Scripting: Comparison Task**

* **Question / Task:** Can you write a shell script to compare three numbers and find the largest of the three numbers?  
  * **Instructor's Suggestion / Feedback:**  
    * Finish it off quickly without wasting time, and keep your servers ready.

### **6\. Linux Administration: Permissions & Keys**

* **Question:** Can you explain all file operators?  
  * **Instructor's Suggestion / Answer:** *(No answer provided by instructor)*  
* **Question:** How can we generate a key pair?  
  * **Instructor's Suggestion / Answer:** *(No answer provided by instructor)*  
* **Question:** How do we give sudo permissions to a user?  
* **Sub-Question:** Why do we use that specific command (`visudo`), and why are we not using `vi`?  
  * **Instructor's Suggestion / Answer:** *(No answer provided by instructor)*

### **7\. Linux File Operations**

* **Question:** What are the different ways we can create a file in Linux?  
* **Sub-Question:** What are the other ways to create a file besides `touch` and `vi`?  
* **Sub-Question:** What is append (`>>`) or redirect (`>`) used for?  
* **Sub-Question:** If a file does not exist, will redirect or append not create the file?  
* **Sub-Question:** What are the other options available to create a file?  
  * **Instructor's Answer / Suggestion:**  
    * In real-time work, `touch` or `vi` are generally not used to create files; redirection (`>`) or append (`>>`) is commonly used.  
    * The `tee` command can also be used to create files.  
    * The `cat` command can also be used to create files.  
    * Spend extra time exploring and testing all options in the environment to gain a deeper understanding.

### **8\. Linux Directory Architecture**

* **Question:** What are the root folders you are aware of in Linux architecture?  
* **Sub-Question:** Can you list the root folder names (e.g., `/var`, `/etc`, `/home`, `/opt`) and explain the purpose of each folder?  
* **Sub-Question:** Have you ever explored the directory structure?  
* **Sub-Question:** Where did you install Tomcat?  
* **Sub-Question:** Why have we installed Tomcat in `/opt`? Why can't we install it in `/etc`, and why are we not keeping it in `/etc`?  
  * **Instructor's Suggestion / Guidance:**  
    * Understand the specific purpose and meaning behind each directory in Linux; there is an intended reason why third-party applications like Tomcat belong in `/opt` rather than configuration folders like `/etc`.

### **9\. Advanced Scripting & Configuration Files**

* **Question:** Can you explain special variables in a shell script?  
  * **Instructor's Suggestion / Answer:** *(No answer provided by instructor)*  
* **Question:** Can you explain the differences between `sed` and `awk`?  
  * **Instructor's Suggestion / Answer:** *(No answer provided by instructor)*  
* **Question:** What is the use of the `.bashrc` file?  
* **Sub-Question:** Why are we setting environment variables and aliases in `.bashrc`? What is the purpose?  
* **Sub-Question:** Do we restart the server every day to delete old or unused files?  
* **Sub-Question:** Why is it specifically placed in `.bashrc` since it is session-based?  
  * **Instructor's Answer:**  
    * Configurations in `.bashrc` (such as aliases and session environment variables) are session-based, so whenever a new session starts, they are automatically initialized.

### **10\. Career Exploration & SRE Concepts**

* **Question:** Do you have any questions?  
  * *(Student asked how to explore more questions/tasks)*  
  * **Instructor's Suggestion / Guidance:**  
    * Search Google for interview questions.  
    * Use ChatGPT to generate practical tasks to practice and understand concepts deeply.  
    * Write clear, specific prompts (e.g., *"give me basic Linux practice tasks"* or *"advanced level tasks"*) rather than restricting it by uploading basic notes.  
* **Question:** Do you know what SRE is and what an SRE does?  
  * **Instructor's Suggestion / Guidance:**  
    * Think at an architectural level and explore the various roles related to DevOps (e.g., Cloud Engineer, SRE) based on core cloud architecture.

# 6\. QA by Krishna 21-Feb-2026 17\_15\_38

### **1\. Shell Scripting: Loop Practice & File Operators**

* **Question:** Have you explored and practiced all the topics covered?  
* **Sub-Question:** Have you practiced the rest of the loops taught in the class (beyond just the for loop)?  
* **Sub-Question:** Will you be able to do any of the tasks requested?  
* **Question:** Can you explain file operators in shell scripting?  
  * **Instructor's Suggestion / Answer:** *(No answer provided by instructor; student explained \-f, \-d, \-r, \-w, \-x, \-e, \-s)*

### **2\. Practical Scripting: File vs. Directory Checking & User Input**

* **Question / Task:** Can you share your screen and write a shell script using any of these file operators?  
* **Sub-Question:** Why are you trying trial-and-error without reading the error properly to see where and what it is showing?  
* **Sub-Question:** The script executed, but why is it showing that the file is not a file?  
  * **Instructor's Suggestion / Feedback:**  
    * Practice thoroughly; practical practice is the only way to understand the underlying reasons for errors.  
* **Sub-Question:** Instead of hardcoding the filename in the script, how can we accept or read it dynamically from the user?  
* **Sub-Question:** How can you modify the script so that if a name is provided, it dynamically checks and identifies whether the given input is a file or a directory?  
* **Sub-Question:** Why are you using double quotes there?

### **3\. Linux Storage: Disk Space, Devices, & Partitions**

* **Question:** How can we check the disk space of the server?  
* **Sub-Question:** Looking at the df \-h output summary, how much space is utilized and how much is left?  
* **Sub-Question:** What are these filesystems displayed in the output?  
* **Sub-Question:** What is the mount point (what are they mounted on)?  
* **Question:** What is the actual disk size attached to the server?  
* **Sub-Question:** What are the three devices shown in the disk output?  
* **Sub-Question:** If you consider them partitions, why are they displayed as devices? What is the difference between a device and a partition?  
* **Question:** You attached an 8 GB volume to this server; how can we increase it?  
* **Sub-Question:** Can you perform the disk increase practically?  
  * **Instructor's Answer / Clarification:**  
    * A device is different from a partition. To get more disk space, you must attach/expand a device; adding a partition does not increase the underlying disk capacity (e.g., an 8 GB disk can simply be divided into multiple partitions based on requirements).  
    * Out of the three displayed devices, the 8 GB device is the root volume attached during server creation; the other two are internal EC2 storage devices, not partitions of the main volume.

### **4\. AWS & Linux Practical Assignment: Volume Resizing & Mounting**

* **Question:** How do we increase the disk space and mount a volume onto a new directory?  
* **Sub-Question (to class/Nagraj):** Who understood the task? What is your understanding of the question?  
  * **Instructor's Practical Tasks Assigned:**  
    * **Task 1:** Increase the existing 8 GB root EBS volume to 10 GB or 12 GB in AWS and expand it at the OS level so it reflects in df \-h.  
    * **Task 2:** Create a brand new EBS volume in AWS (e.g., 2 GB, 5 GB, or 10 GB), attach it to the running EC2 instance, and mount it to a newly created folder.  
    * Both volumes must be visible and properly mounted when running df \-h.  
    * Run and understand the underlying Linux commands involved (lsblk, mount, filesystem creation, etc.) rather than merely creating volumes in the AWS console.

### **5\. Shell Scripting: Loops & Numerical Logic**

* **Question:** Can you explain the difference between a while loop and while read line?  
* **Sub-Question:** Why do we use a while loop? Can you provide an example?  
* **Question / Task:** Can you open a notepad and write a script to print only the even numbers from 0 up to a user-provided number $N$ (e.g., up to 100)?  
* **Sub-Question:** What did you practice over the weekend if you are struggling with basic loop scripts?  
* **Question / Task:** Can you write a script to identify whether a given number is a prime number?  
  * **Instructor's Clarification:**  
    * 0 and 1 are not prime numbers.  
* **Question / Task:** Can you write a script to check whether a given number is odd or not?  
* **Sub-Question:** What does the \$ (dollar symbol) represent in the script argument/variable?  
* **Sub-Question:** How do we properly use that syntax?  
  * **Instructor's Feedback:**  
    * Syntax must be checked carefully; in shell scripting, formatting and spaces matter significantly.

### **6\. Linux Memory Management: Swap Space**

* **Question:** Can you show the swap memory on your server?  
* **Sub-Question:** What does the swap output mean?  
* **Sub-Question:** It is currently showing 0 0 0 0; how can we enable swap space on the server?  
* **Question:** What is the purpose of swap space, and in what real-time scenarios is it used?  
* **Sub-Question:** If multiple applications are running on a server without swap space enabled, how are they running?  
* **Sub-Question:** What is the trigger point that causes processes to be moved into swap space?  
  * **Instructor's Answer:**  
    * Memory exhaustion (when physical RAM is exhausted) is the trigger point; the operating system then moves idle/inactive processes to swap memory.  
* **Sub-Question:** Where does swap memory come from physically?  
  * **Instructor's Answer / Clarification:**  
    * Swap memory comes from the disk space (storage). Focus on how the operating system handles it at the OS level rather than attributing it to cloud providers like AWS.

### **7\. Shell Scripting: Relational Operators & Conditional Branching**

* **Question / Task:** Can you write a script to determine whether a given number is above 100, below 100, or equal to 100?  
* **Question:** Can you explain relational operators in shell scripting?  
* **Sub-Question:** What relational operators are you using in your script?  
* **Sub-Question:** What is stored inside that variable/string?  
* **Sub-Question:** If the input number 100 is supplied, what will the current script logic print?  
* **Sub-Question:** Why would the script throw an error if the condition simply evaluates to false?  
* **Sub-Question:** If the condition 100 \> 100 is evaluated, does it pass? If not, what gets printed next?  
* **Sub-Question:** Why wasn't this logical flow applied initially?  
* **Question:** Can you write a script comparing three numbers?  
* **Question:** Can you print even numbers up to a specified number?  
  * **Instructor's Learning Path Guidance:**  
    * Follow a structured progression: Start with basic echo, advance to if and if-else, then master loops (while, while read, for). Do not remain stuck on basic conditionals.  
* **Sub-Question:** Can you write the loop syntaxes properly from memory?

### **8\. Server Monitoring: Load Average & Server Logs**

* **Question / Task:** Can you execute the conditional script on the server and verify the output?  
* **Question:** How do you check the load average of the server?  
* **Sub-Question:** How do you view the load average live in real time?  
* **Question:** Where can we find the server log files?  
* **Question:** What is the file size of the script you created?  
* **Question:** How can you locate all files ending with the .log extension across the server?  
* **Sub-Question:** Was the find command not taught in the class? Why wasn't it utilized properly?  
  * **Instructor's Feedback:**  
    * Every command taught must be practiced and understood thoroughly to know what it does and why it works.

### **9\. Practical Scripting: File Validation & Permissions**

* **Question / Task:** Can you write a script that takes a file name as input (e.g., abc.txt), checks whether the file exists, and if it exists, verifies whether it has read permissions?  
* **Sub-Question:** Why are you creating a file inside the script rather than checking the input provided?  
* **Sub-Question:** Where is the logic checking whether the file has readable permissions or not?  
* **Sub-Question:** Did you not attend classes or take notes?  
  * **Instructor's Feedback:**  
    * Do not offer excuses like receiving late permissions; prepare and practice professionally.  
* **Sub-Question:** What specific topics do you currently know in shell scripting?

### **10\. Linux Command Line: Log Inspection, Grep, & Ownership**

* **Question / Task:** Can you use the find command to locate all files with the .log extension?  
* **Question / Task:** Can you pick any log file and print the last 20 lines (or last 50 lines)?  
* **Question / Task:** How can you search for any error messages across all of those discovered log files?  
* **Sub-Question:** If you pipe the output of the find command directly into grep error, where is it checking for the error message?  
  * **Instructor's Clarification:**  
    * Piping the output of find into grep only filters the file path strings generated by find; it does not search inside the actual contents of each individual file. Think through the command pipeline logically.  
* **Question / Task:** Can you switch to the root user?  
* **Question / Task:** Can you create a folder and list its details using ls \-l?  
* **Sub-Question:** Who is the current owner of that newly created folder?  
* **Question / Task:** How can you change the ownership of that folder to ec2-user?  
  * **Instructor's Overall Performance Feedback:**  
    * Performance was below expectations; daily performance is being tracked and scored. Everyone will be monitored closely over the next 7 days, and those whose performance graphs do not improve will be moved to the non-placement batch. Complete all assignments shared by the team.

### **11\. DevOps Career Paths & Industry Preparation**

* **Question:** Do you have any questions?  
  * *(Student asked about the class schedule for the next day)*  
  * **Instructor's Answer:** Class will be held the next day, likely around 5:30 PM.  
* **Question (Student inquiry on career profiles & market expectations):** What roles exist and what level of preparation is needed?  
  * **Instructor's Guidance / Explanation:**  
    * **Market Roles:** The DevOps domain encompasses multiple distinct roles, including Site Reliability Engineer (SRE), Cloud Engineer, DevOps Engineer, Cloud Architect, and DevSecOps.  
    * **Role Differences:** DevSecOps focuses heavily on security and networking; SRE centers on system monitoring, reliability, production setup, and resolving live operational issues.  
    * **Target Preparation:** Prepare comprehensively for advanced requirements equivalent to 5 to 7 years of industry experience across architecture, monitoring, and automation.  
* **Question:** How many days has it been since the course started?  
  * **Instructor's Guidance:**  
    * It has been less than one month; there are several months remaining to build depth. Focus strictly on mastering the practical class lessons, resolving QA queries, and completing hands-on assignments.

Here is the complete extraction of all questions and sub-questions asked by the instructor during this session, along with any suggestions, answers, or practical tasks provided directly by the instructor from the transcript.

### **1\. Shell Scripting: Loop Practice & File Operators**

* **Question:** Have you practiced with the rest of the loops taught in the class (beyond just the for loop)?  
* **Sub-Question:** Will you be able to do any of the tasks requested?  
* **Question:** Can you explain file operators in shell scripting?  
  * **Instructor's Suggestion / Answer:** *(No answer provided by instructor; student listed \-f, \-d, \-r, \-w, \-x, \-e, \-s)*

### **2\. Practical Scripting: File vs. Directory Checking & User Input**

* **Question / Task:** Can you please share your screen and write a shell script using any of these file operators?  
* **Sub-Question:** Why are you trying trial-and-error instead of doing it confidently? Did you read the error properly to see where and what it is showing?  
* **Sub-Question:** The script executed, but why is it showing that the file is not a file?  
  * **Instructor's Suggestion / Feedback:**  
    * If you practice thoroughly, you will understand the why, what, and how behind errors.  
* **Sub-Question:** Instead of hardcoding/passing the file name inside the script, how can we ask the user and read it dynamically?  
* **Sub-Question:** If a name is given, how can the script check and identify whether it is a file or a directory? Can we do that?  
* **Sub-Question:** Why are you using double quotes there?

### **3\. Linux Storage: Disk Space, Devices, & Partitions**

* **Question:** How can we check the disk space of the server?  
* **Sub-Question:** Looking at the df \-h output summary, how much space is utilized and how much is left?  
* **Sub-Question:** What are these filesystems displayed in the output?  
* **Sub-Question:** What are they mounted on (what is the mount point)?  
* **Question:** What is the disk size attached to the server?  
* **Sub-Question:** Can you explain in detail how it works and what the three devices shown in fdisk are?  
* **Sub-Question:** If you consider them partitions, why are they displayed as devices? What is the difference between a device and a partition?  
* **Question:** An 8 GB volume is attached to this server; how can we increase it?  
* **Sub-Question:** Can you perform the disk increase practically?  
  * **Instructor's Answer / Clarification:**  
    * A device is different from a partition. To get more disk space, you need to attach/increase a device; adding a partition does not increase total disk size (e.g., an 8 GB disk can simply be divided into smaller partitions based on requirements).  
    * Out of the three displayed devices, the 8 GB device is the volume attached during server creation; the other two are internal EC2 storage devices, not partitions of your main disk.

### **4\. AWS & Linux Practical Assignment: Volume Resizing & Mounting**

* **Question:** How do we increase the disk space, and how do we mount it onto a new folder?  
* **Sub-Question (to Nagraj / class):** Who understood the task? Nagraj, what is your understanding of the question?  
* **Sub-Question:** Can you summarize your understanding of the task rather than reciting the step-by-step console clicks?  
  * **Instructor's Practical Tasks Assigned:**  
    * **Task 1:** Increase the existing root EBS volume from 8 GB to 10 GB or 12 GB in AWS and expand it at the operating system level so the increase reflects in df \-h.  
    * **Task 2:** Create an additional EBS volume in AWS (e.g., 2 GB, 5 GB, or 10 GB), attach it to the same running EC2 instance, and mount it to a newly created folder.  
    * Both volumes must be active and verified using df \-h.  
    * Understand and execute the required Linux operating system commands (lsblk, mount, etc.) rather than just provisioning volumes in the AWS console.

### **5\. Shell Scripting: Loop Syntax & Numerical Logic**

* **Question:** Can you explain the difference between a while loop and while read?  
* **Sub-Question:** Why do we use a while loop? Can you give one example?  
* **Question / Task:** Can you share your screen, open notepad, and write a script to print only even numbers from 0 up to a user-specified number $N$ (e.g., up to 100)?  
* **Sub-Question:** What did you learn and practice over the weekend if you have not practiced loops and shell scripting is about to conclude?  
* **Question / Task:** Can you write a script to identify whether a given number is a prime number?  
  * **Instructor's Clarification:**  
    * 0 and 1 are not prime numbers.  
* **Question / Task:** Can you write a script to check whether a given number is odd or not?  
* **Sub-Question:** What is \$1 (dollar one)?  
  * **Instructor's Feedback:**  
    * Syntaxes must be checked very carefully; in shell scripting, formatting and spaces matter significantly.  
* **Sub-Question:** How do we write that simple logic without overthinking it?

### **6\. Linux Memory Management: Swap Space**

* **Question:** Can you open your server and show the swap memory?  
* **Sub-Question:** Can you demonstrate it live on the server?  
* **Sub-Question:** What does swap memory mean?  
* **Question:** It is currently displaying 0 0 0 0; how can we enable swap space?  
* **Sub-Question:** What have you done to enable it?  
* **Question:** What is the purpose of swap space, and in what real-time scenarios is it used?  
* **Sub-Question:** If multiple applications are running on a server without swap space enabled, how are they running?  
* **Sub-Question:** What is the exact trigger point that causes processes to be moved into swap space?  
  * **Instructor's Answer:**  
    * Memory exhaustion (when physical RAM is exhausted) is the trigger point; the operating system then moves processes to swap memory.  
* **Sub-Question:** Where does swap memory physically come from?  
  * **Instructor's Answer / Clarification:**  
    * Swap memory comes from the disk space (storage). Understand this mechanism at the operating system level rather than attributing it specifically to AWS or cloud providers.  
  * **Instructor's Warning / Feedback:**  
    * Focus, practice, and prepare; marks are deducted for every unanswered question.

### **7\. Practical Scripting: Conditional Number Comparison**

* **Question / Task:** Can you share your screen, open notepad, and write a script to identify whether a given number is above 100 or below 100?

# 7\. QA by Krishna 22-Feb-2026 17\_02\_17

### **1\. Assignment Status & Linux Volume Expansion**

* **Primary Question:** Have you completed the assignment to increase the disk space?  
  * **Sub-question:** Why didn't you complete it?  
  * **Sub-question:** Nagas, what about you?  
* **Question / Task:** Can you please explain what you have done?  
* **Question / Task:** It is currently 12 GB; can you increase it to 15 GB and show me?  
* **Core Technical Question:** If a production server is running and cannot be stopped or restarted, how do you increase the disk space online without stopping or rebooting the server?  
  * **Instructor's Note / Clarification:** Increasing disk space via the AWS Management Console alone is not the objective. From a Linux administration perspective, stopping/restarting an instance is not acceptable for production workloads; the file system/volume expansion must be handled inside the running OS without downtime.  
* **Sub-question:** How did you attach a new volume? Was that done using the same process?  
* **Question / Task:** What did you do after creating and attaching the volume?  
* **Question / Task:** Can you create a small volume (e.g., 5 GB or 6 GB) right now and attach it?  
* **Sub-question:** What does that command do?  
* **Sub-question:** What is `xdc`?  
* **Sub-question:** What happens if you restart your system now?  
* **Sub-question:** Why are we entering it into the file system table (`/etc/fstab`)? What does the `2` represent at the end of the entry?  
  * **Instructor's Observation / Clarification:** The entry above also has a `2`. Furthermore, the third entry is not a root partition. Explore how to manage and mount partitions properly and how disk space expansion is carried out inside Linux.

### **2\. Shell Scripting: Special Variables (`$*` vs `$@`)**

* **Primary Question:** What is the difference between `$*` and `$@` in shell scripting?  
  * **Sub-question:** When you say they report status, what status do they report?  
  * **Follow-up Question / Task:** Can you share your screen, open Notepad, and demonstrate how they work with a real-time practical example?  
  * **Sub-question:** What will `$*` print, and what will `$@` print?  
  * **Sub-question:** If you pass arguments `2 3 4`, where will it print `2 3 4`?  
  * **Sub-question:** When executing `echo "The passed arguments are in string: $*"`, what will that statement print?  
  * **Sub-question:** What will the line with `$@` print?  
  * **Sub-question:** If both print `2 3 4`, what is the actual difference between them, and why do we use one over the other?  
  * **Instructor's Technical Clarification:**  
    * Simply memorizing a one-line definition (that `$*` treats all arguments as a single string while `$@` treats them as separate arguments/array elements) without understanding their execution behavior is insufficient.  
    * When quoted inside loops (`"$*"` vs `"$@"`), `"$*"` combines all positional parameters into a single string separated by the first character of `IFS`, whereas `"$@"` preserves each positional parameter as an independent quoted argument (`"$1"` `"$2"` `"$3"`...).

### **3\. Practice Scripts & Control Structures**

* **Question / Task:** What shell scripts have you practiced? Can you show the scripts executed directly on your server (rather than written in local notes)?  
* **Question / Task:** Can you write down the syntax for a `while` loop?  
* **Primary Question:** In what scenarios do we use a `while` loop?  
  * **Sub-question:** Can you provide a concrete example?  
  * **Instructor's Technical Definition & Clarification:**  
    * A `while` loop is used to perform a repetitive task or continuously iterate through a block of code as long as a specified condition remains true, terminating once the condition evaluates to false.  
    * Answers must be articulated using proper technical terminology (conditions, evaluation, loop termination, iterative execution) rather than vague conversational phrasing.

### **4\. Process Management**

* **Primary Question:** What is a zombie process?  
  * **Answer Provided in Session:** A zombie process (defunct process) is a process that has completed execution, but its exit status remains in the process table because its parent process has not yet read it via the `wait()` system call.

### **5\. Script Debugging Flags (`set -x` and `set -e`)**

* **Primary Question:** How do you debug your shell scripts?  
  * **Sub-question:** When using `set -e`, what does it mean when you say a "non-zero argument is executed"? Does that mean exit status codes like 1, 2, etc.?  
  * **Sub-question:** If a shell script is run with `set -x`, what happens during execution, and how does the script execute line by line?  
  * **Sub-question:** Can we explain the functionality properly using standard technical terminology?  
  * **Instructor's Technical Clarification & Answer:**  
    * **`set -x` (xtrace / trace mode):** Used to debug scripts line by line. It expands and displays each command and its arguments to standard error before executing it, allowing you to trace the exact execution flow.  
    * **`set -e` (errexit / exit on error):** Causes the shell script to terminate immediately if any command returns a non-zero exit status (indicating failure), preventing the script from proceeding with subsequent commands when an error occurs.

# 8\. QA by Krishna 24-Feb-2026 19\_01\_52
**Part 1: Scripting, Commands, and Linux Basics**

* Can you explain the passwordless connection process? How can we establish a passwordless connection between servers?  
* What is the difference between a for loop and a while loop?  
* Can you share your screen of the notepad?  
* Can you please open a notepad and write a script to print all even numbers up to the given number? (Suppose if I give input as 100, so it should print from 0 to 100 at all even numbers.)  
* Do you understand my question?  
* Can you print all the numbers from one to a given n number? (You don't have to print an even number, just print all the numbers. Suppose if I give 10 as an input, it should print from 1 to 10\. Can you do that?)  
* What is this? I didn't ask something which is not difficult. I'm asking to print 1 to 10 numbers while that is also not \[working\]?  
* Can you write the while loop syntax?  
* Can you explain what it is? Write some condition at least. What will it print here? Run this.  
* Do you understand the logic of how the while loop is working? Do you understand now?  
* In a similar way, why can't we print 1 to n numbers?  
* What command do we use to print? What command do we use to print any number or anything?  
* Why do we use the `echo` command?  
* Here you are using the `echo` command \[for the sum\], so why can't we use `echo` to print the number?  
* Can you please print numbers from one to a given n number, only odd numbers? I don't want all the numbers.  
* Run it. Show me the output.  
* Can you write a syntax for a for loop?  
* Can you explain the differences between a soft link and a hard link?  
* Can you explain special variables?  
* Can you please share your screen and open a note?  
* Can you please write a script where there is a file which has some content, and I need to pick each line and find out the number of characters in that particular line? Did you understand my question?  
* Execute it and show me the output.  
* Can you write all the file operators in a notepad and explain what each does?  
* How can we find and replace a word in a file? How can we do that?  
* Write a script to add all even numbers up to the given n. (For example, if I give 10 as an input, it should add 2, 4, 6, 8, and 10 and give the addition of all these values.)

**Part 2: AWS / Server Operations & Process**

* What/where are you getting confused?  
* So then how do we do it?  
* Have you done the assignment which I asked you to do and share in the group?  
* Can you tell me the steps, how can we do that \[increase the disk space\]?  
* Why do we need to stop the instance?  
* If we stop the instance, then there is no point, right?  
* Have you done it? Can you explain it to them?  
* First of all, explain the disadvantages of stopping and then increasing the volume, and then come to the point of why we need to do this.  
* How did you do that? In which process did you do it? Did you stop the server?

