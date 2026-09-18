# Shell Script Commands Cheat Sheet

> Essential Bash scripting commands, built-ins, parameter expansions, string manipulations, and error handling syntax.

| Command | Description & AI Explanation | Category / Tags |
| :--- | :--- | :--- |
| `set -euo pipefail` | Strict Bash execution mode: exits immediately on command error (-e), treats unset variables as errors (-u), and fails pipeline if any command fails (-o pipefail). | Error Handling, Best Practice |
| `trap 'echo "Error on line $LINENO: exit code $?" >&2' ERR` | Registers an error trap that automatically prints the exact line number and failing exit status whenever any command returns a non-zero exit code. | Debugging, Traps |
| `trap 'rm -rf "$TEMP_DIR"' EXIT` | Registers a clean-up handler executed on script termination regardless of whether it exited normally, received SIGINT, or threw an error. | Clean-up, Robustness |
| `VAR="${MY_VAR:-default_value}"` | Parameter expansion: assigns 'default_value' to VAR if MY_VAR is unset or null without throwing an unbound variable error. | Parameter Expansion |
| `: "${DATABASE_URL:?Error: DATABASE_URL must be exported}"` | Verifies mandatory environment variable existence; aborts script with the specified error message if unset or empty. | Validation, Safe Scripts |
| `FILE_EXT="${FILENAME##*.}"` | Parameter expansion: strips longest prefix ending in '.' to cleanly extract the file extension without spawning an external process like awk or cut. | String Manipulation |
| `BASENAME="${FULL_PATH##*/}"` | Extracts the filename from a full path using pure Bash expansion (faster alternative to basename binary). | String Manipulation |
| `DIRNAME="${FULL_PATH%/*}"` | Extracts the parent directory path from a full path using pure Bash expansion (faster alternative to dirname binary). | String Manipulation |
| `if [[ "$STR" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then ...` | Performs native regex pattern matching in double brackets [[ ]] to validate IPv4 address format without calling grep. | Regex, Conditionals |
| `while IFS= read -r line \|\| [ -n "$line" ]; do ... done < file.txt` | Robust line-by-line file reader preserving whitespace and handling files missing a final newline character. | File I/O, Loops |
| `read -s -p "Enter Secret Token: " USER_TOKEN` | Securely prompts user for credentials while disabling terminal echo (-s), preventing token display on the terminal or shell history. | Security, User Input |
| `exec 3>&1 4>&2 >/var/log/script.log 2>&1` | Redirects all script stdout and stderr to a log file while preserving original terminal descriptors on file descriptors 3 and 4. | Redirection, Logging |
| `nohup ./long_task.sh > output.log 2>&1 &` | Launches background process immune to SIGHUP (terminal disconnect), redirecting all stdout/stderr to output.log and returning terminal control. | Background Jobs |
| `wait $PID` | Pauses script execution until background process with given PID completes, capturing its return exit status into $?. | Process Control, Concurrency |
| `declare -A CONFIG_MAP=([env]="prod" [region]="us-east-1")` | Declares an associative array (hashmap / dictionary) in Bash 4+ for key-value configuration lookups. | Arrays, Data Structures |
| `for key in "${!CONFIG_MAP[@]}"; do echo "$key => ${CONFIG_MAP[$key]}"; done` | Iterates over all keys in an associative array, safely handling whitespace within values. | Arrays, Loops |
| `timeout 15s curl -f https://internal.healthcheck/status` | Executes a health check with a strict 15-second cutoff; terminates process with exit code 124 if it exceeds the duration. | Networking, Automation |
| `command -v jq >/dev/null 2>&1 \|\| { echo "jq required"; exit 1; }` | Checks whether an external binary (jq) is available in the current PATH before script execution proceeds. | Dependency Verification |
| `printf '%-20s %-10s %s\n' "Service" "Status" "Port"` | Formats table-style output with column padding and strict alignment for terminal reports. | Formatting, Output |
| `diff -u <(sort list1.txt) <(sort list2.txt)` | Uses process substitution <(...) to sort and compare two files on the fly without generating intermediate scratch files on disk. | Process Substitution, Diff |
