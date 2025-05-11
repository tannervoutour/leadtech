#!/usr/bin/env python3
"""
Test script to send a mock payload to the webhook endpoint.
This allows testing of the webhook without running the full memory cron job.
"""

import json
import requests
import argparse
from datetime import datetime

# Webhook URL - Same as in the production script
WEBHOOK_URL = "https://tannervoutour1.app.n8n.cloud/webhook/ff9d72c1-2364-410a-bbd7-ee9c84a13458"

def create_mock_payload(workspace_id="1", thread_id="default", workspace_name="Test Workspace", user_name="test_user"):
    """
    Create a mock payload similar to what the main script would send
    """
    current_time = datetime.now().isoformat()
    
    payload = {
        "conversation": "User: What is the weather today?\n\nAssistant: It's sunny with a high of 75°F.\n\nUser: Will it rain tomorrow?\n\nAssistant: There's a 30% chance of rain tomorrow afternoon.",
        "workspaceID": workspace_id,
        "threadID": thread_id,
        "user": user_name,
        "createdAt": current_time,
        "workspace": workspace_name,
        "summary": ""
    }
    
    return payload

def send_mock_payload(payload, silent=False):
    """
    Send the mock payload to the webhook endpoint
    """
    if not silent:
        print("Sending mock payload to webhook:")
        print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        result = response.json() if response.text.strip() else {}
        
        if not silent:
            print("\nWebhook response:")
            print(json.dumps(result, indent=2))
            
        return result
    except requests.RequestException as e:
        print(f"Error sending payload: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return None

def main():
    """
    Main function to parse arguments and run the test
    """
    parser = argparse.ArgumentParser(description='Test webhook endpoint with a mock payload.')
    parser.add_argument('--workspace-id', type=str, default="1", help='Workspace ID (default: 1)')
    parser.add_argument('--thread-id', type=str, default="default", help='Thread ID (default: default)')
    parser.add_argument('--workspace-name', type=str, default="Test Workspace", help='Workspace name (default: Test Workspace)')
    parser.add_argument('--user-name', type=str, default="test_user", help='User name (default: test_user)')
    parser.add_argument('--silent', action='store_true', help='Run in silent mode (minimal output)')
    parser.add_argument('--count', type=int, default=1, help='Number of payloads to send (default: 1)')
    parser.add_argument('--custom-webhook', type=str, help='Custom webhook URL to use instead of the default')
    
    args = parser.parse_args()
    
    global WEBHOOK_URL
    if args.custom_webhook:
        WEBHOOK_URL = args.custom_webhook
    
    if not args.silent:
        print(f"Using webhook URL: {WEBHOOK_URL}")
    
    results = []
    for i in range(args.count):
        if not args.silent and args.count > 1:
            print(f"\nSending payload {i+1}/{args.count}:")
        
        payload = create_mock_payload(
            workspace_id=args.workspace_id,
            thread_id=args.thread_id,
            workspace_name=args.workspace_name,
            user_name=args.user_name
        )
        
        result = send_mock_payload(payload, silent=args.silent)
        results.append(result)
    
    # Print summary for multiple payloads
    if args.count > 1 and not args.silent:
        print(f"\nSent {args.count} payloads to webhook.")
        success_count = sum(1 for r in results if r is not None)
        print(f"Success: {success_count}, Failed: {args.count - success_count}")

if __name__ == "__main__":
    main()