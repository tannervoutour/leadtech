# Memory Cron Job Production Setup

This document provides instructions for setting up the memory cron job on the production server.

## Changes Made in This Implementation

1. **Directory Structure**:
   - Created a dedicated directory for the memory cron job at `/scripts/memory_cron/`
   - Added data subdirectory for persistent storage of JSON files
   - Added logs subdirectory for execution logs
   - Created a shell wrapper script for reliable execution with logging

2. **Python Script Modifications**:
   - Updated script to use relative paths based on the script's location
   - All data files are now stored in the `data/` subdirectory
   - All logs are stored in the `logs/` subdirectory with timestamps
   - The script will create necessary directories if they don't exist
   - Conversations are now grouped by workspace ID, thread ID, and a rolling time window
   - Script now runs daily at 3 AM CST rather than hourly
   - Removed unnecessary fields from payload (previous_user_ai, previous_chunk_text, chunk_text)

3. **Added Documentation**:
   - README.md with explanation of the script's purpose and setup
   - crontab_entry.txt with the crontab entry for reference
   - This PRODUCTION_SETUP.md file for production deployment guidance

## Production Server Setup Steps

1. **Copy Code**:
   The code should be in the same relative location on the production server as on the development server:
   ```
   /path/to/project/scripts/memory_cron/
   ```

2. **Configuration**:
   Review and update these variables in `getchat.py` for production:
   - `API_KEY`: Verify this is the correct API key for production
   - `BASE_URL`: Update to production API endpoint
   - `WEBHOOK_URL`: Update to production webhook URL
   - `CONVERSATION_HOUR_WINDOW`: Adjust if needed (currently set to 1 hour)

3. **Test Run**:
   Before setting up the cron job, do a test run:
   ```bash
   cd /path/to/project/scripts/memory_cron/
   ./run_memory_cron.sh
   ```
   
   Check the logs directory to verify everything worked correctly.

4. **Set Up Cron Job**:
   Add the cron job to run at 3 AM CST (9 AM UTC):
   ```bash
   crontab -e
   ```
   
   Add this line (update the path to match your production server):
   ```
   0 9 * * * /path/to/project/scripts/memory_cron/run_memory_cron.sh
   ```

5. **Verify Logs and Data**:
   After the first run, check:
   - `/path/to/project/scripts/memory_cron/logs/` for execution logs
   - `/path/to/project/scripts/memory_cron/data/` for the JSON data files

6. **Monitor**:
   You may want to set up monitoring to ensure the cron job runs successfully:
   - Check for new log files being created daily
   - Verify the data files are being updated

## Maintenance Notes

- **Log Rotation**: The script automatically removes logs older than 30 days
- **Data Persistence**: All processed conversation data is stored in the data directory
- **Conversation Tracking**: The script tracks processed conversations to avoid duplicate entries
- **Error Handling**: The script logs all errors to the log files
- **Testing**: If you need to test changes, you can run the script manually using `./run_memory_cron.sh`

## Conversation Definition

In this implementation, a "conversation" is defined by:
1. A unique combination of workspace ID and thread ID
2. Messages occurring within a rolling 1-hour window of each other

The rolling window approach means:
- If a message occurs within 1 hour of the previous message in the same workspace/thread, it's considered part of the same conversation
- If a message occurs more than 1 hour after the previous message, it starts a new conversation
- This allows for continuous conversations that span multiple hours, as long as no gap exceeds 1 hour

For example:
- Message at 1:00 PM → Conversation A starts
- Message at 1:45 PM → Added to Conversation A (within 1 hour of previous)
- Message at 2:30 PM → Added to Conversation A (within 1 hour of previous)
- Message at 4:00 PM → Conversation B starts (gap > 1 hour)

## Payload Structure

The payload sent to the webhook endpoint includes:
- conversation: Full text of the conversation
- workspaceID: ID of the workspace
- threadID: ID of the thread
- user: Username
- createdAt: Creation timestamp
- workspace: Name of the workspace
- summary: Summary of the conversation (initially empty, filled by webhook response)

The previous fields `previous_user_ai`, `previous_chunk_text`, and `chunk_text` have been removed as requested.