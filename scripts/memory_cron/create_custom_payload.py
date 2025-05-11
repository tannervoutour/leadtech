#!/usr/bin/env python3
"""
Script to create and send a custom payload to the webhook endpoint.
This allows you to specify a custom conversation text and other payload properties.
"""

import json
import requests
import argparse
from datetime import datetime
import sys

# Webhook URL - Same as in the production script
WEBHOOK_URL = "https://tannervoutour1.app.n8n.cloud/webhook/ff9d72c1-2364-410a-bbd7-ee9c84a13458"

def create_custom_payload(conversation_text, workspace_id="1", thread_id="default", 
                         workspace_name="Test Workspace", user_name="test_user"):
    """
    Create a custom payload with user-provided conversation text
    """
    current_time = datetime.now().isoformat()
    
    payload = {
        "conversation": conversation_text,
        "workspaceID": workspace_id,
        "threadID": thread_id,
        "user": user_name,
        "createdAt": current_time,
        "workspace": workspace_name,
        "summary": ""
    }
    
    return payload

def send_payload(payload):
    """
    Send the payload to the webhook endpoint
    """
    print("Sending custom payload to webhook:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        result = response.json() if response.text.strip() else {}
        
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
    parser = argparse.ArgumentParser(description='Send a custom payload to the webhook endpoint.')
    parser.add_argument('--workspace-id', type=str, default="1", help='Workspace ID (default: 1)')
    parser.add_argument('--thread-id', type=str, default="default", help='Thread ID (default: default)')
    parser.add_argument('--workspace-name', type=str, default="Test Workspace", help='Workspace name (default: Test Workspace)')
    parser.add_argument('--user-name', type=str, default="test_user", help='User name (default: test_user)')
    parser.add_argument('--conversation-file', type=str, help='Path to a file containing the conversation text')
    parser.add_argument('--custom-webhook', type=str, help='Custom webhook URL to use instead of the default')
    
    args = parser.parse_args()
    
    global WEBHOOK_URL
    if args.custom_webhook:
        WEBHOOK_URL = args.custom_webhook
    
    print(f"Using webhook URL: {WEBHOOK_URL}")
    
    # Get conversation text
    if args.conversation_file:
        try:
            with open(args.conversation_file, 'r', encoding='utf-8') as f:
                conversation_text = f.read()
        except Exception as e:
            print(f"Error reading conversation file: {e}")
            sys.exit(1)
    else:
        print("Enter conversation text (end with Ctrl+D on a new line):")
        conversation_text = sys.stdin.read()
    
    # Create and send payload
    payload = create_custom_payload(
        conversation_text=conversation_text,
        workspace_id=args.workspace_id,
        thread_id=args.thread_id,
        workspace_name=args.workspace_name,
        user_name=args.user_name
    )
    
    send_payload(payload)

if __name__ == "__main__":
    main()