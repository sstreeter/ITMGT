# ITMGT - Inventory Management for Lab Computers

This guide will help you set up the **Server** (on AlmaLinux) and the **Client** (on Windows) from scratch.

---

## Part 1: Server Setup (AlmaLinux)

**Goal:** Get the server running so it can listen for inventory reports.

### Step 1: Install System Tools
Log in to your AlmaLinux server. We need `git` (to download this code) and `python3` (to run it).
Run these commands one by one:

```bash
# Update the system to make sure we are fresh
sudo dnf update -y

# Install Git, Python3, capability tools, and OpenSSL
sudo dnf install -y git python3 python3-pip libcap openssl
```

### Step 2: Create the "Service User"
We creates a special user called `sbsmgr` to run the app. This is safer than running as root!
```bash
# Create the user (system account, no login)
sudo useradd -r -s /sbin/nologin sbsmgr

# Create the folder where the database will live (Recommended: /var/lib/sbs-inventory)
# Note: The code lives in /opt, but the data should live here to avoid permission issues.
sudo mkdir -p /var/lib/sbs-inventory
sudo chown -R sbsmgr:sbsmgr /var/lib/sbs-inventory
sudo chmod 700 /var/lib/sbs-inventory
```

### Step 3: Get the Code onto the Server
**Option A: If using Git (Recommended)**
```bash
# Clone the repository to /opt
sudo git clone <your-repo-url> /opt/sbs-inventory/ITMGT

# Give YOU ownership of the code (so you can 'git pull' without sudo)
sudo chown -R $USER:$USER /opt/sbs-inventory/ITMGT

# Generate Self-Signed Certificates (for HTTPS)
# NOTE: In production, install real certs to /opt/sbs-inventory/ITMGT/
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /opt/sbs-inventory/ITMGT/server.key \
    -out /opt/sbs-inventory/ITMGT/server.crt

# Ensure the Service User (sbsmgr) can read the keys!
sudo chown sbsmgr:sbsmgr /opt/sbs-inventory/ITMGT/server.key /opt/sbs-inventory/ITMGT/server.crt
sudo chmod 640 /opt/sbs-inventory/ITMGT/server.key
```

**Option B: Copying files from your computer (SCP)**
If the code is on your laptop and you need to push it to the server:
1.  Open a terminal on your **laptop**.
2.  Run this command to copy *only* the server files (Replace `user@server-ip` with your login):
    ```bash
    # We only send the files the server needs. We SKIP the client scripts and local secrets (.env).
    scp sbs-receiver.py requirements.txt .env.example sbs-receiver.service user@server-ip:/tmp/
    ```
3.  Go back to your **server** terminal and move them to the final spot:
    ```bash
    sudo mkdir -p /opt/sbs-inventory/ITMGT
    sudo mv /tmp/sbs-receiver.py /tmp/requirements.txt /tmp/.env.example /tmp/sbs-receiver.service /opt/sbs-inventory/ITMGT/
    sudo chown -R sbsmgr:sbsmgr /opt/sbs-inventory
    ```


### Step 4: Install Python Dependencies
We use a "Virtual Environment" (venv) to keep our Python libraries tidy.
```bash
cd /opt/sbs-inventory/ITMGT

# Create the virtual environment
sudo python3 -m venv venv

# Activate it and install libraries
sudo ./venv/bin/pip install -r requirements.txt
```

### Step 5: The "Hall Pass" (Port 443)
By default, Linux forbids regular users (like `sbsmgr`) from using ports below 1024 (like 443). We need to give Python a "Hall Pass" (Capability) to do this.
```bash
# Find the REAL python executable inside our venv
REAL_PYTHON=$(readlink -f ./venv/bin/python3)

# Grant the capability
sudo setcap 'cap_net_bind_service=+ep' $REAL_PYTHON
```

### Step 6: Secrets (.env)
We need to set the secret password that clients use to talk to the server.
1.  Copy the example file:
    ```bash
    sudo cp .env.example .env
    # IMPORTANT: Update the SBS_DB_FILE path!
    # Open .env and set: SBS_DB_FILE=/var/lib/sbs-inventory/inventory.db
    nano .env
    ```
2.  **Generate a Secure Key**:
    We included a script to do this for you!
    ```bash
    chmod +x set_api_key.py
    ./set_api_key.py
    ```
    *It will print the new key. **Copy this key** because you will need it for the Windows clients!*

### Step 7: Turn it on (Systemd)
We want this to run automatically when the server turns on.
1.  Copy the service file:
    ```bash
    sudo cp sbs-receiver.service /etc/systemd/system/
    # IMPORTANT: Start Gunicorn with SSL arguments!
    # Edit the file and ensure ExecStart looks like this:
    # ExecStart=/opt/sbs-inventory/ITMGT/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:443 --certfile=/opt/sbs-inventory/ITMGT/server.crt --keyfile=/opt/sbs-inventory/ITMGT/server.key sbs-receiver:app
    sudo nano /etc/systemd/system/sbs-receiver.service
    ```
2.  Tell Systemd to read the new file:
    ```bash
    sudo systemctl daemon-reload
    ```
3.  Enable it at boot and start it now:
    ```bash
    sudo systemctl enable --now sbs-receiver
    ```
4.  Check if it's working:
    ```bash
    sudo systemctl status sbs-receiver
    ```
    *You should see a green "active (running)" light.*

### Step 8: Network & Firewall
By default, the firewall blocks outside connections. Open it up!
```bash
# Allow HTTPS traffic
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Verify you can reach it locally
curl -k https://127.0.0.1/
# (Should return "404 Not Found" - this is success!)
```

---

## Part 2: Client Setup (Windows)

**Goal:** Configure the Windows PC to send its info to the server.

### Step 1: Prepare the Files
1.  Create a folder on the C: drive: `C:\IT_Management`
1.  Create a folder on the C: drive: `C:\IT_Management`
2.  Copy these **TWO** files into it (Delete any others like `sbs-inv-smb.ps1`):
    *   `sbs-inv-https.ps1` (The script)
    *   `config.json` (The settings)

### Step 2: Configure
Open `config.json` with Notepad.
*   **ServerUrl**: Change `your-server-address` to the server's REAL IP (e.g. `192.168.1.50`).
    *   Example: `"https://192.168.1.50/checkin"` (Do NOT use `127.0.0.1` or port `:5000`).
*   **ApiKey**: Paste the SAME secret string you put in the `.env` file on the server.

### Step 3: Run
1.  Right-click **PowerShell** -> **Run as Administrator**.
2.  Type:
    ```powershell
    C:\IT_Management\sbs-inv-https.ps1
    ```
3.  If successful, you will see green text saying "Success".