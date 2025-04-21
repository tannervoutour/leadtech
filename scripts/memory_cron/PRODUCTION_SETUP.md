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
   - `TIME_GAP_THRESHOLD_SECONDS`: Adjust if needed (currently set to 60 seconds)

3. **Test Run**:
   Before setting up the cron job, do a test run:
   ```bash
   cd /path/to/project/scripts/memory_cron/
   ./run_memory_cron.sh
   ```
   
   Check the logs directory to verify everything worked correctly.

4. **Set Up Cron Job**:
   Add the cron job to run hourly:
   ```bash
   crontab -e
   ```
   
   Add this line (update the path to match your production server):
   ```
   0 * * * * /path/to/project/scripts/memory_cron/run_memory_cron.sh
   ```

5. **Verify Logs and Data**:
   After the first run, check:
   - `/path/to/project/scripts/memory_cron/logs/` for execution logs
   - `/path/to/project/scripts/memory_cron/data/` for the JSON data files

6. **Monitor**:
   You may want to set up monitoring to ensure the cron job runs successfully:
   - Check for new log files being created every hour
   - Verify the data files are being updated

## Maintenance Notes

- **Log Rotation**: The script automatically removes logs older than 30 days
- **Data Persistence**: All processed conversation data is stored in the data directory
- **Error Handling**: The script logs all errors to the log files
- **Testing**: If you need to test changes, you can run the script manually using `./run_memory_cron.sh`