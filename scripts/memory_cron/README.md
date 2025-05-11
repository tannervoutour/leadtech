# Memory Cron Job

This directory contains the memory processing cron job that runs daily at 3 AM CST to fetch chat data and process it for memory retention.

## Purpose

The script fetches all chat data from the API and groups conversations based on workspace ID, thread ID, and a rolling time window. It processes these conversations and sends them to a webhook endpoint that handles memory processing. Each conversation is tracked to ensure it's only processed once, preventing duplicate entries across days.

## Directory Structure

- `getchat.py` - Main Python script that fetches and processes chat data
- `run_memory_cron.sh` - Shell wrapper script to run the Python script with logging
- `data/` - Directory where JSON data files are stored
- `logs/` - Directory where log files are stored
- `PRODUCTION_SETUP.md` - Detailed production setup instructions
- `crontab_entry.txt` - The crontab entry to use

## Setup Cron Job

To set up the cron job to run daily at 3 AM CST (9 AM UTC):

```bash
crontab -e
```

Add the following line:

```
0 9 * * * /home/tanner_outour/leadtech/scripts/memory_cron/run_memory_cron.sh
```

For production server, update the path to match your server's directory structure.

## Configuration

The script uses these key configuration variables:

- API_KEY - Your API key for authentication
- BASE_URL - The API endpoint URL
- WEBHOOK_URL - The webhook URL to send processed data
- CONVERSATION_HOUR_WINDOW - Time window in hours to consider messages part of the same conversation (default: 1)

Update these values in the `getchat.py` file for your environment.

## How It Works

1. The script fetches all chats from the API endpoint
2. Chats are grouped by workspace ID and thread ID
3. Within each workspace/thread group, messages are further grouped by a rolling time window
   - Messages within 1 hour of each other are considered part of the same conversation
   - If messages are more than 1 hour apart, they start a new conversation
4. Each unique conversation is processed and sent to the webhook
5. The script maintains a record of processed conversations to avoid duplicates
6. Logs are generated in the `logs/` directory with timestamps

## Rolling Time Window Explanation

The script uses a rolling time window approach to group messages into conversations:

1. Messages are sorted by timestamp within each workspace/thread group
2. The first message starts a new conversation
3. Each subsequent message is compared to the timestamp of the previous message
4. If the time difference is less than 1 hour, the message is added to the current conversation
5. If the time difference is greater than 1 hour, the message starts a new conversation

Example:
- Message 1: 10:00 AM → Start Conversation A
- Message 2: 10:30 AM → Add to Conversation A (within 1 hour of Message 1)
- Message 3: 11:20 AM → Add to Conversation A (within 1 hour of Message 2)
- Message 4: 12:45 PM → Start Conversation B (more than 1 hour after Message 3)
- Message 5: 1:15 PM → Add to Conversation B (within 1 hour of Message 4)

This ensures that continuous conversations are grouped together, regardless of fixed hour boundaries.

## Testing

To run the script manually and test:

```bash
./run_memory_cron.sh
```

Check the logs directory for execution logs and the data directory for JSON data files.