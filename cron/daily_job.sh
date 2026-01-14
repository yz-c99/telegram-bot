#!/bin/bash
#
# Daily job script for Telegram to Google Docs Auto-Collector
# This script is executed by cron every day at 9:00 AM
#

# Change to project directory
cd /home/user/test

# Activate virtual environment
source venv/bin/activate

# Run the main script
python src/main.py >> logs/cron.log 2>&1

# Exit with the status of the main script
exit $?
