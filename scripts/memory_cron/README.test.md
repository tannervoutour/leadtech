# Testing the Memory Cron Job

This directory includes test scripts to verify the webhook functionality without running the full memory cron job.

## Test Scripts

### 1. Simple Webhook Test

The `test_webhook.py` script sends a simple mock payload to the webhook endpoint:

```bash
# Basic usage
./test_webhook.py

# With custom workspace and thread IDs
./test_webhook.py --workspace-id 5 --thread-id 123 --workspace-name "Production Line" --user-name "operator"

# Send multiple test payloads
./test_webhook.py --count 3

# Use a different webhook URL
./test_webhook.py --custom-webhook "https://your-webhook-url.com/endpoint"

# Silent mode (minimal output)
./test_webhook.py --silent
```

### 2. Custom Payload Test

The `create_custom_payload.py` script lets you create a more customized payload:

```bash
# Using keyboard input
./create_custom_payload.py
# (Then type your conversation and press Ctrl+D when done)

# Using a text file with conversation content
./create_custom_payload.py --conversation-file sample_conversation.txt

# With custom parameters
./create_custom_payload.py --workspace-id 10 --thread-id "special" --conversation-file sample_conversation.txt
```

## Sample Files

- `sample_conversation.txt`: A simple example conversation that can be used with the custom payload script

## Troubleshooting

If you encounter issues with the webhook:

1. Check the webhook URL is correct
2. Verify your network connection can reach the webhook endpoint
3. Examine any error messages in the script output
4. Try a simpler payload to isolate the problem

## Webhook Response Format

The webhook should respond with a JSON object containing:

```json
{
  "Memory": "Memory summary text goes here",
  "Status": "true/false"
}
```

If you receive a different response format, the webhook endpoint may have changed or be malfunctioning.