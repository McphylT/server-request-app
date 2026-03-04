# =============================================================
#  STEP 1 — Connect to your Linux server via SSH
# =============================================================
# On Windows: Open "Command Prompt" or "PowerShell" and type:
ssh your-username@your-server-ip
# Example: ssh admin@192.168.1.50
# Enter your password when prompted.


# =============================================================
#  STEP 2 — Install Python and required tools
# =============================================================
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv

# Confirm Python installed correctly (should print a version number):
python3 --version


# =============================================================
#  STEP 3 — Create a folder for the app
# =============================================================
sudo mkdir -p /opt/provisioning-api
sudo chown $USER:$USER /opt/provisioning-api
cd /opt/provisioning-api

# You are now "inside" the app folder. All next steps happen here.


# =============================================================
#  STEP 4 — Upload your files
# =============================================================
# You need to get main.py and requirements.txt onto the server.
# The easiest way (no extra software needed) is to create
# each file directly on the server using the commands below.

# --- Create requirements.txt ---
cat > requirements.txt << 'EOF'
fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic[email]==2.7.1
EOF

# --- Create main.py ---
# Copy the full contents of main.py from the artifact above,
# then run this command. It will open a blank editor:
nano main.py
# Paste the code (right-click to paste in most SSH clients).
# When done: press Ctrl+O to save, then Ctrl+X to exit.


# =============================================================
#  STEP 5 — Set up a Python virtual environment
# =============================================================
# A virtual environment is just an isolated space for the app's
# packages so they don't interfere with anything else.

python3 -m venv venv

# Activate it:
source venv/bin/activate
# You'll notice "(venv)" appears at the start of your prompt.

# Install the required packages:
pip install -r requirements.txt
# This will download and install FastAPI, Uvicorn, and Pydantic.


# =============================================================
#  STEP 6 — Test the app runs correctly
# =============================================================
uvicorn main:app --host 0.0.0.0 --port 8000

# Open a browser and visit:  http://your-server-ip:8000/docs
# You should see a green "Server Provisioning API" page.
# If it works — press Ctrl+C to stop it. We'll run it properly next.


# =============================================================
#  STEP 7 — Run the app as a background service (auto-start)
# =============================================================
# This makes the app start automatically every time the server
# reboots, and keeps it running in the background.

# Create the service file:
sudo nano /etc/systemd/system/provisioning-api.service

# Paste the contents from the "provisioning-api.service" artifact.
# Save with Ctrl+O, exit with Ctrl+X.

# Enable and start the service:
sudo systemctl daemon-reload
sudo systemctl enable provisioning-api
sudo systemctl start provisioning-api

# Check it's running (look for "active (running)" in green):
sudo systemctl status provisioning-api


# =============================================================
#  STEP 8 — Configure Nginx Proxy Manager
# =============================================================
# 1. Open your Nginx Proxy Manager dashboard in a browser.
# 2. Go to "Proxy Hosts" → click "Add Proxy Host".
# 3. Fill in the values from the "Nginx Proxy Manager Settings"
#    artifact exactly as shown.
# 4. Click "Save". NPM will auto-issue your SSL certificate.
#
# Once saved, visit: https://srv-req.persol.net/docs
# You should see the live API documentation page over HTTPS.


# =============================================================
#  STEP 9 — View submitted requests
# =============================================================
# After requesters fill out and submit the form, you can view
# all submissions by visiting this URL in your browser:

# All submissions:
https://srv-req.persol.net/api/requests

# One specific submission (replace 1 with the ID number):
https://srv-req.persol.net/api/requests/1

# To approve/reject, use the interactive docs page:
https://srv-req.persol.net/docs


# =============================================================
#  HANDY COMMANDS (for later use)
# =============================================================

# Restart the API after any changes:
sudo systemctl restart provisioning-api

# View live logs (useful for troubleshooting):
sudo journalctl -u provisioning-api -f

# Stop the service:
sudo systemctl stop provisioning-api
