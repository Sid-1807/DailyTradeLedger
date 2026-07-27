#!/bin/bash

# Absolute path to DailyTradeLedger project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PYTHON_BIN="$PROJECT_DIR/venv/bin/python3"
MAIN_SCRIPT="$PROJECT_DIR/main.py"
LOG_FILE="$PROJECT_DIR/logs/cron.log"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "Error: Virtual environment python non-existent at $PYTHON_BIN"
    echo "Please set up virtual environment first."
    exit 1
fi

CRON_CMD="0 21 * * 1-5 $PYTHON_BIN $MAIN_SCRIPT --daily >> $LOG_FILE 2>&1"

# Check if cron job already exists
(crontab -l 2>/dev/null | grep -F "$MAIN_SCRIPT") >/dev/null
if [ $? -eq 0 ]; then
    echo "Cron job for DailyTradeLedger already exists in crontab."
else
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "Cron job installed successfully:"
    echo "$CRON_CMD"
fi
