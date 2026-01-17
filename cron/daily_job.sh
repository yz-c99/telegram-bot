#!/bin/bash
#
# Daily job script for Telegram to Google Docs Auto-Collector
# This script is executed by cron every day at 9:00 AM
#

# Set error handling
set -e

# Project directory
PROJECT_DIR="/Users/r/Claude/telegram-bot"

# Change to project directory
cd "$PROJECT_DIR"

# Log start time
echo "============================================================"
echo "Daily Job Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"

# Activate virtual environment
source "$PROJECT_DIR/venv/bin/activate"

# Run the main script
python3 "$PROJECT_DIR/src/main.py"

# Log completion
echo "============================================================"
echo "Daily Job Completed: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo ""

# Exit with the status of the main script
exit $?
