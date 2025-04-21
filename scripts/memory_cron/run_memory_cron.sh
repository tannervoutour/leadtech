#!/bin/bash
# Script to run memory cron job with proper logging

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"
PYTHON_SCRIPT="$SCRIPT_DIR/getchat.py"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Create data directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/data"

# Set log filename with timestamp
LOG_FILE="$LOG_DIR/memory_cron_$(date +\%Y\%m\%d_\%H\%M\%S).log"

# Run the Python script and log output
echo "Starting memory cron job at $(date)" > "$LOG_FILE"
python3 "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1
EXIT_CODE=$?
echo "Memory cron job completed at $(date) with exit code $EXIT_CODE" >> "$LOG_FILE"

# If we want to keep only the last 30 log files
find "$LOG_DIR" -name "memory_cron_*.log" -type f -mtime +30 -delete

exit $EXIT_CODE