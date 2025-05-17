# ExploitFarm Python Library and CLI

**ExploitFarm** is an advanced tool designed to manage exploits and flag submissions in Attack-Defense CTF competitions. It combines a Python library with a command-line interface (CLI), providing flexibility and efficiency for managing CTF tasks. This documentation provides a comprehensive overview of its features, installation, and usage.

---

## **Key Features**

- **Multi-Threaded Execution**: Utilize a pool of worker threads for efficient exploit execution.

- **Exploit Management**: Initialize, push, pull, and version control exploit source code.

- **Attack Groups**: Collaborate and manage group-based attacks.

- **Integrated Status Monitoring**: View real-time server and current execution statuses.

---

## **Installation**

Install ExploitFarm via pip:

```bash
pip3 install -U xfarm && xfarm --install-completion
```

For Windows, use:

```bash
python -m xfarm
```

**Prerequisites**:

- Python 3.8+
- Compatible with Linux, macOS, and Windows.
- Ensure you have `pip` installed.

---

## **Getting Started**

ExploitFarm provides both programmatic and CLI access to its features.

### **Programmatic API**

The Python library allows developers to integrate ExploitFarm functionality into their scripts:

```python
import random
from exploitfarm import *

host = get_host()  # Retrieves the server host (from environment variables or configuration)
print(f"Connected to {host}")

flags = [random_str(32) + "=" for _ in range(10)]
print(f"Submitting flags: {flags}")
submit_flags(flags)
```

#### **Store Class**

The `Store` class provides a key-value storage system for exploits, allowing you to save and retrieve centralized data during execution.
The key value store is different for each exploit id. You can use it to store some data you need to save and change for every exploit execution.

```python
from exploitfarm import Store

store = Store()

# Set a value
store.set("example_key", {"example": "data"})

# Get a value
data = store.get("example_key")
print(data)

# Delete a key
store.delete("example_key")

# List all keys
keys = store.keys()
print(keys)
```

**Methods**:

- `get(key: str, timeout: int = HTTP_TIMEOUT) -> bytes`: Retrieve a value by key.
- `set(key: str, value: bytes, timeout: int = HTTP_TIMEOUT)`: Store a value by key.
- `delete(key: str, timeout: int = HTTP_TIMEOUT)`: Delete a key.
- `keys(timeout: int = HTTP_TIMEOUT) -> list[str]`: List all stored keys.

**Environment Variables Required**:

- `XFARM_REMOTE_URL`: Base URL for the exploit storage API.
- `XFARM_EXPLOIT_ID`: Unique identifier for the exploit.
- `XFARM_LOGIN_TOKEN`: Authentication token for secure access.

### **Command-Line Interface (CLI)**

The CLI is the primary way to interact with ExploitFarm for exploit and attack management.

#### **CLI Syntax**

```bash
xfarm [COMMAND] [OPTIONS]
```

Use `--help` to view available commands and options:

```bash
xfarm --help
```

---

## **Detailed CLI Documentation**

### **Global Options**

These options are applicable to all commands:

- `-h`, `--help`: Display help information for a command.
- `-I`, `--no-interactive`: Disable interactive configuration mode (default: interactive).
- `-v`, `--version`: Show the version of the ExploitFarm client.

---

### **Primary Commands**

#### **Start Exploit**

Run an exploit from the specified path:

```bash
xfarm start [OPTIONS] PATH
```

**Options**:

- `PATH`: The directory containing the exploit (default: current directory).
- `--pool-size, -p`: Fixed size for the thread pool (default: `10 * CPU cores`).
- `--submit-pool-timeout`: Timeout (in seconds) for the submission pool (default: 3).
- `--test, -t`: Test the exploit without submission.
- `--test-timeout`: Timeout for exploit testing (default: 30 seconds).
- `--no-auto-push, -n`: Prevent automatic source push.
- `--push-message, -m`: Custom message for the source push.

**Example**:

```bash
xfarm start ./my_exploit --pool-size 20 --test
```

---

#### **Status**

Retrieve the status of the server or specific components:

```bash
xfarm status [WHAT]
```

**Options**:

- `WHAT`: Specify the status type (default: `status`). Available options include:
  - `status`: General server status.
  - `submitters`: Submission system details.
  - `services`: Active services.
  - `exploits`: Exploit statuses.
  - `flags`: Flag submission statistics.
  - `teams`: Team information.
  - `clients`: Client configuration details.

**Example**:

```bash
xfarm status exploits
```

---

### **Configuration Commands**

#### **Edit Configuration**

Edit client settings:

```bash
xfarm config edit [OPTIONS]
```

**Options**:

- `--address`: Server address.
- `--port`: Server port.
- `--nickname`: Client nickname.
- `--https`: Use HTTPS (default: False).

**Example** (no interactive mode):

```bash
xfarm -I config edit --address example.com --port 443 --https --nickname
```

#### **Reset Configuration**

Reset all client settings to their default values:

```bash
xfarm config reset
```

---

#### **Login**

Authenticate with the server:

```bash
xfarm config login [OPTIONS]
```

**Options**:

- `--password`: Provide the password directly.
- `--stdin`: Read the password from stdin.

#### **Logout**

Logout from the server:

```bash
xfarm config logout
```

---

### **Exploit Management Commands**

#### **Initialize Exploit**

Set up a new exploit project:

```bash
xfarm exploit init [OPTIONS]
```

**Options**:

- `--edit, -e`: Edit the configuration interactively.
- `--name`: Exploit name.
- `--service`: Associated service UUID.
- `--language`: Programming language.

#### **Push Exploit**

Upload the exploit source code to the server:

```bash
xfarm exploit push [OPTIONS]
```

**Options**:

- `--message, -m`: Commit message.
- `--force, -f`: Force push even with an old commit has the same source.

#### **Retrieve Exploit Information**

Get details about the exploit source:

```bash
xfarm exploit info [OPTIONS]
```

**Options**:

- `--raw, -r`: Display raw JSON response.

#### **Update Exploit**

Update to the latest commit:

```bash
xfarm exploit update [OPTIONS]
```

**Options**:

- `--force, -f`: Force update.

#### **Download Exploit**

Download the exploit source:

```bash
xfarm exploit download [OPTIONS]
```

**Options**:

- `--folder, -f`: Specify target folder.
- `--commit-uuid`: Commit ID (default: latest).

---

### **Attack Group Commands**

#### **Create Attack Group**

Create a new group for collaborative attacks (and also join in it if in interactive mode):

```bash
xfarm group create [OPTIONS]
```

**Options**:

- `--name`: Group name.
- `--current-commit`: Use the current exploit commit.
- `--submit-pool-timeout`: Timeout for submission pooling.

#### **Join Attack Group**

Join an existing attack group:

```bash
xfarm group join [OPTIONS]
```

**Options**:

- `--group`: Group ID.
- `--queue`: Queue number for the group.
- `--trigger-start`: Start the attack after joining.

---

## **Environment Variables**

Environment variables can simplify configuration:

- `XFARM_HOST`: Server address.
- `XFARM_PORT`: Server port.
- `XFARM_INTERACTIVE`: Enable or disable interactive mode.
- `XFARM_REMOTE_URL`: API Base URL for remote exploit storage.
- `XFARM_EXPLOIT_ID`: Unique identifier for the exploit.
- `XFARM_LOGIN_TOKEN`: Authentication token for secure access.

---

## **Best Practices**

1. Use `--test` to verify exploits before running them in production.
2. Regularly push changes to the server for version control (they are auto-pushed on attack start anyway).
3. Collaborate using attack groups for efficient resource utilization if the attack is heavy to execute.

---

For further assistance, visit the [GitHub repository](https://github.com/pwnzer0tt1/exploitfarm) or consult the community resources.

