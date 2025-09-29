#!/bin/bash

# === CONFIGURATION ===
APP_DIR="/home/ec2-user/rent-finder-bot"
SERVICE_DIR="/etc/systemd/system/"
SERVICE_NAME="rentfinderbot.service"
BRANCH="main"
PYTHON_ENV="$APP_DIR/venv/bin/python"

# === SCRIPT ===
set -e

echo ">>> Updating $SERVICE_NAME ..."

cd "$APP_DIR"

echo ">>> Pulling latest code from $BRANCH ..."
git fetch origin
git reset --hard origin/$BRANCH

echo ">>> Installing dependencies ..."
if [ -f "requirements.txt" ]; then
    $PYTHON_ENV -m pip install -r requirements.txt --upgrade
fi

echo ">>> Reloading systemd service ..."
sudo systemctl daemon-reexec
sudo systemctl reload-or-restart "$SERVICE_NAME"

echo ">>> Checking service status ..."
sudo systemctl status "$SERVICE_NAME" --no-pager --full

echo ">>> Update complete!"
