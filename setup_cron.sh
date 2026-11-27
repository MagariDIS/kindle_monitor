#!/bin/bash
# Kindle Monitor - Cron Setup Script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_TEMPLATE="$SCRIPT_DIR/.env.kindle.template"
ENV_FILE="$HOME/.env.kindle"
WRAPPER_SCRIPT="$SCRIPT_DIR/run_kindle_display.sh"

echo "=========================================="
echo "Kindle Monitor - Cron Job Setup"
echo "=========================================="
echo ""

# Step 1: Check if environment file exists
if [ -f "$ENV_FILE" ]; then
    echo "✓ $ENV_FILE already exists"
    echo "  (Skipping environment file creation)"
else
    echo "Step 1: Creating environment file"
    echo "--------"

    if [ ! -f "$ENV_TEMPLATE" ]; then
        echo "ERROR: Template file not found: $ENV_TEMPLATE"
        exit 1
    fi

    cp "$ENV_TEMPLATE" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "✓ Created: $ENV_FILE (permissions: 600)"
    echo ""
    echo "IMPORTANT: Edit $ENV_FILE and replace the placeholder with your actual API key:"
    echo "  nano $ENV_FILE"
    echo ""
    read -p "Press Enter after you've set the API key..."
fi

# Step 2: Verify wrapper script
echo ""
echo "Step 2: Verifying wrapper script"
echo "--------"
if [ ! -f "$WRAPPER_SCRIPT" ]; then
    echo "ERROR: Wrapper script not found: $WRAPPER_SCRIPT"
    exit 1
fi

if [ ! -x "$WRAPPER_SCRIPT" ]; then
    chmod +x "$WRAPPER_SCRIPT"
    echo "✓ Made executable: $WRAPPER_SCRIPT"
else
    echo "✓ Wrapper script is executable: $WRAPPER_SCRIPT"
fi

# Step 3: Create log directory
echo ""
echo "Step 3: Setting up log directory"
echo "--------"

# Try system log first
if sudo touch /var/log/kindle_monitor.log 2>/dev/null; then
    sudo chown $USER:$USER /var/log/kindle_monitor.log
    echo "✓ Log file: /var/log/kindle_monitor.log"
    LOG_DIR="/var/log"
else
    # Fall back to home directory
    mkdir -p "$HOME/logs"
    echo "✓ Log directory: $HOME/logs"
    LOG_DIR="$HOME/logs"
fi

# Step 4: Add to crontab
echo ""
echo "Step 4: Adding to crontab"
echo "--------"

# Check if job already exists
if crontab -l 2>/dev/null | grep -q "run_kindle_display.sh"; then
    echo "✓ Cron job already exists"
    echo ""
    echo "Current entry:"
    crontab -l 2>/dev/null | grep "run_kindle_display.sh"
else
    # Add the job
    (crontab -l 2>/dev/null || echo "# Crontab for Kindle Monitor") > /tmp/crontab.tmp
    echo "" >> /tmp/crontab.tmp
    echo "# Kindle Monitor - Display update every 15 minutes" >> /tmp/crontab.tmp
    echo "*/15 * * * * source ~/.env.kindle 2>/dev/null && $WRAPPER_SCRIPT" >> /tmp/crontab.tmp

    crontab /tmp/crontab.tmp
    rm /tmp/crontab.tmp

    echo "✓ Added cron job: every 15 minutes"
    echo ""
    echo "Entry:"
    crontab -l 2>/dev/null | grep "run_kindle_display.sh"
fi

# Step 5: Test run
echo ""
echo "Step 5: Test run"
echo "--------"
echo "Running once to verify configuration..."
echo ""

source "$ENV_FILE" 2>/dev/null || true
$WRAPPER_SCRIPT

# Step 6: Summary
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "✓ Environment file: $ENV_FILE"
echo "✓ Wrapper script: $WRAPPER_SCRIPT"
echo "✓ Log location: $LOG_DIR/kindle_monitor.log"
echo "✓ Cron interval: every 15 minutes (*/15 * * * *)"
echo ""
echo "Next runs:"
date -d "+15 minutes" "+  %Y-%m-%d %H:%M"
date -d "+60 minutes" "+  %Y-%m-%d %H:%M"
echo ""
echo "Monitor logs:"
echo "  tail -f $LOG_DIR/kindle_monitor.log"
echo ""
echo "To stop the job:"
echo "  crontab -e  # then comment out or delete the line"
echo ""
