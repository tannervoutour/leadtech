# Memory Cron Job

This directory contains the memory processing cron job that runs hourly to fetch chat data and process it for memory retention.

## Directory Structure

- `getchat.py` - Main Python script that fetches and processes chat data
- `run_memory_cron.sh` - Shell wrapper script to run the Python script with logging
- `data/` - Directory where JSON data files are stored
- `logs/` - Directory where log files are stored

## Setup Cron Job

To set up the cron job to run hourly:

```bash
crontab -e
```

Add the following line:

```
0 * * * * /home/tanner_outour/leadtech/scripts/memory_cron/run_memory_cron.sh
```

For production server, update the path to match your server's directory structure.

## Configuration

The script uses these key configuration variables:

- API_KEY - Your API key for authentication
- BASE_URL - The API endpoint URL
- WEBHOOK_URL - The webhook URL to send processed data
- TIME_GAP_THRESHOLD_SECONDS - Time threshold to start a new conversation chunk

Update these values in the `getchat.py` file for your environment.