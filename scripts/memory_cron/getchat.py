import json
import requests
from datetime import datetime, timedelta
import os
import time

# ----- CONFIGURATION -----
API_KEY = "D12M59S-TCJ416W-NE8QN2N-0PGRQAY"
BASE_URL = "https://app.leadtechai.net/api"
WEBHOOK_URL = "https://tannervoutour1.app.n8n.cloud/webhook/ff9d72c1-2364-410a-bbd7-ee9c84a13458"

# Files for persistence:
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
PROCESSED_FILE = os.path.join(DATA_DIR, "processed_conversations.json")
MEMORIES_FILE = os.path.join(DATA_DIR, "conversation_memories.json")

# Define the time window for grouping conversations (in hours)
CONVERSATION_HOUR_WINDOW = 1  # Messages within 1 hour of each other are considered the same conversation

# ----- HELPER FUNCTIONS -----
def load_json_file(filepath, default):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {filepath}: {e}")
                return default
    return default


def save_json_file(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def ensure_file_exists(filepath, default):
    """If the file doesn't exist, create it with the default content."""
    if not os.path.exists(filepath):
        print(f"{filepath} does not exist. Creating file with default content.")
        save_json_file(filepath, default)


def parse_date(date_str):
    """Convert an ISO 8601 date string to a naive datetime (strip offsets and microseconds)."""
    if not date_str:
        return datetime.min
    if date_str.endswith("Z"):
        date_str = date_str[:-1] + "+00:00"
    dt = datetime.fromisoformat(date_str)
    return dt.replace(tzinfo=None, microsecond=0)


def format_date(dt: datetime) -> str:
    """Convert datetime back to ISO string (without microseconds)."""
    return dt.replace(microsecond=0).isoformat()


def fetch_all_chats():
    """
    Retrieves all chats from the API endpoint.
    This function calls the workspace-chats API.
    """
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    })
    print("[DEBUG] Making API call to /v1/admin/workspace-chats ...")
    resp = session.post(f"{BASE_URL}/v1/admin/workspace-chats")
    print("[DEBUG] Status code:", resp.status_code)
    print("[DEBUG] Raw response (first 500 chars):", resp.text[:500])
    resp.raise_for_status()
    data = resp.json()
    return data.get("chats", [])


def group_chats_by_thread(chats):
    """
    Group raw chat items by (workspaceId, thread_id).
    Return a dict of { f"{ws_id}_{thread_id}": [chat1, chat2, ...], ... }
    """
    grouped = {}
    for chat in chats:
        ws_id = chat.get("workspaceId")
        thread_id = chat.get("thread_id") or "default"
        if not ws_id:
            continue
        key = f"{ws_id}_{thread_id}"
        grouped.setdefault(key, []).append(chat)
    for key in grouped:
        grouped[key].sort(key=lambda c: parse_date(c.get("createdAt", "")))
    return grouped


def create_conversation_id(workspace_id, thread_id, conversation_date):
    """Create a unique conversation ID based on workspace, thread, and conversation date."""
    date_part = conversation_date.strftime('%Y%m%d%H%M%S')
    return f"{workspace_id}_{thread_id}_{date_part}"


def group_by_rolling_window(messages, max_gap_hours=CONVERSATION_HOUR_WINDOW):
    """
    Group messages using a rolling time window.
    Messages that are within max_gap_hours of each other are considered part of the same conversation.
    
    Args:
        messages: List of messages sorted by timestamp
        max_gap_hours: Maximum time gap in hours between messages to be considered the same conversation
        
    Returns:
        List of conversation groups (each group is a list of messages)
    """
    if not messages:
        return []
    
    # Convert max_gap_hours to seconds
    max_gap_seconds = max_gap_hours * 3600
    
    # Initialize the first conversation group
    conversations = [[messages[0]]]
    last_msg_time = parse_date(messages[0].get("createdAt", ""))
    
    # Group subsequent messages
    for msg in messages[1:]:
        msg_time = parse_date(msg.get("createdAt", ""))
        
        # Calculate time difference in seconds
        time_diff = (msg_time - last_msg_time).total_seconds()
        
        # If within the time window, add to current conversation
        if time_diff <= max_gap_seconds:
            conversations[-1].append(msg)
        # Otherwise, start a new conversation group
        else:
            conversations.append([msg])
        
        # Update the last message time
        last_msg_time = msg_time
    
    return conversations


def group_chats_by_conversation(chats):
    """
    Group chats by conversation, where a conversation is defined by:
    - Same workspace ID and thread ID
    - Messages occurring within the rolling hour window of each other
    
    Returns a dict of {conversation_id: [chat1, chat2, ...], ...}
    """
    # First group by workspace and thread
    thread_groups = group_chats_by_thread(chats)
    
    # Then further group by rolling time window
    conversation_groups = {}
    for thread_key, thread_messages in thread_groups.items():
        ws_id, thread_id = thread_key.split("_", 1)
        
        # Apply rolling window grouping
        conversations = group_by_rolling_window(thread_messages, CONVERSATION_HOUR_WINDOW)
        
        # Create a conversation ID for each group
        for i, conv_messages in enumerate(conversations):
            if not conv_messages:
                continue
                
            # Use the first message's timestamp for the conversation ID
            first_msg_time = parse_date(conv_messages[0].get("createdAt", ""))
            conv_id = create_conversation_id(ws_id, thread_id, first_msg_time)
            
            # Add a sequence number to ensure uniqueness
            if conv_id in conversation_groups:
                conv_id = f"{conv_id}_{i}"
                
            conversation_groups[conv_id] = conv_messages
    
    return conversation_groups


def build_conversation_text(messages):
    """
    Build a conversation string from the messages.
    """
    conversation_lines = []
    for msg in messages:
        user_text = (msg.get("prompt") or "").strip()
        raw_assistant = (msg.get("response") or "").strip()
        assistant_text = raw_assistant
        try:
            parsed = json.loads(raw_assistant)
            if "text" in parsed:
                assistant_text = parsed["text"].strip()
        except (json.JSONDecodeError, TypeError):
            pass
        
        if user_text:
            conversation_lines.append(f"User: {user_text}")
        if assistant_text:
            conversation_lines.append(f"Assistant: {assistant_text}")
    
    return "\n\n".join(conversation_lines)


def build_conversation_payload(conversation_id, messages):
    """
    Build the payload for a conversation.
    Excludes previous_user_ai, previous_chunk_text, and chunk_text fields as requested.
    """
    if not messages:
        return None
    
    # Get the first message for metadata
    first_msg = messages[0]
    
    # Extract workspace_id and thread_id from conversation_id
    parts = conversation_id.split("_")
    workspace_id = parts[0]
    thread_id = parts[1]
    
    # Get other metadata from the first message
    workspace_name = first_msg.get("workspace", {}).get("name", "Default Workspace")
    user_name = first_msg.get("user", {}).get("username", "")
    created_at = first_msg.get("createdAt", "")
    
    # Build the full conversation text
    conversation_text = build_conversation_text(messages)
    
    # Build the payload (excluding the fields mentioned)
    payload = {
        "conversation": conversation_text,
        "workspaceID": workspace_id,
        "threadID": thread_id,
        "user": user_name,
        "createdAt": created_at,
        "workspace": workspace_name,
        "summary": ""
    }
    
    return payload


def is_conversation_processed(conv_id, processed_conversations):
    """
    Check if a conversation has already been processed by comparing message content.
    """
    # Direct match on conversation ID
    if conv_id in processed_conversations:
        return True
        
    # Extract the base parts (workspace_id, thread_id) for partial matching
    base_parts = "_".join(conv_id.split("_")[:2])
    
    # Check for partial matches with date comparison
    for processed_id in processed_conversations:
        if processed_id.startswith(base_parts):
            return True
            
    return False


def load_processed_conversations():
    """
    Load previously processed conversations.
    Returns a set of conversation_ids that have been processed.
    """
    data = load_json_file(PROCESSED_FILE, {"processed": []})
    processed_set = set()
    
    for item in data.get("processed", []):
        # Get the conversation ID if available
        if "conversationId" in item:
            processed_set.add(item["conversationId"])
        else:
            # For backwards compatibility, construct ID from components
            ws_id = item.get("workspaceId")
            thread_id = item.get("thread_id")
            processed_time = parse_date(item.get("processedTime", ""))
            
            if ws_id and thread_id and processed_time != datetime.min:
                # Use the processed time as part of the ID
                conv_id = create_conversation_id(ws_id, thread_id, processed_time)
                processed_set.add(conv_id)
    
    return processed_set


def save_processed_conversations(processed_set, new_conversations):
    """
    Update the processed conversations file with newly processed conversations.
    """
    data = load_json_file(PROCESSED_FILE, {"processed": []})
    current_records = data.get("processed", [])
    
    # Add new conversations to the records
    for conv_id, payload in new_conversations.items():
        parts = conv_id.split("_")
        if len(parts) >= 3:
            ws_id = parts[0]
            thread_id = parts[1]
            
            # Get the timestamp from the last message in the conversation
            current_records.append({
                "workspaceId": ws_id,
                "thread_id": thread_id,
                "processedTime": datetime.now().replace(microsecond=0).isoformat(),
                "conversationId": conv_id
            })
    
    # Save updated records
    save_json_file(PROCESSED_FILE, {"processed": current_records})


def main():
    """
    Main function to process chat conversations.
    This will:
    1. Fetch all chats
    2. Group them by conversation (workspace+thread+rolling time window)
    3. Process only conversations that haven't been processed before
    4. Send conversation payloads to the webhook
    5. Update the processed conversations record
    """
    print(f"[INFO] Starting chat processing at {datetime.now().isoformat()}")
    
    # Ensure data files exist
    ensure_file_exists(PROCESSED_FILE, {"processed": []})
    ensure_file_exists(MEMORIES_FILE, {"memories": []})
    
    # Load previously processed conversations
    processed_conversations = load_processed_conversations()
    print(f"[INFO] Found {len(processed_conversations)} previously processed conversations")
    
    # Load existing memories
    memories_data = load_json_file(MEMORIES_FILE, {"memories": []})
    memories_list = memories_data.get("memories", [])
    
    try:
        # Fetch all chats
        chats = fetch_all_chats()
        print(f"[INFO] Retrieved {len(chats)} chat(s) from API")
        
        # Group chats by conversation
        conversation_groups = group_chats_by_conversation(chats)
        print(f"[INFO] Grouped into {len(conversation_groups)} conversations")
        
        # Prepare to track newly processed conversations
        new_conversations = {}
        
        # Set up a session for API calls
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        })
        
        # Process each conversation
        for conv_id, messages in conversation_groups.items():
            # Skip already processed conversations
            if is_conversation_processed(conv_id, processed_conversations):
                print(f"[INFO] Skipping already processed conversation: {conv_id}")
                continue
            
            # Build payload for this conversation
            payload = build_conversation_payload(conv_id, messages)
            if not payload:
                continue
            
            print(f"[INFO] Processing conversation {conv_id} with {len(messages)} messages")
            
            # Send payload to webhook
            try:
                print(f"[DEBUG] Sending payload for conversation {conv_id}")
                response = session.post(WEBHOOK_URL, json=payload)
                response.raise_for_status()
                
                # Parse response
                result = response.json() if response.text.strip() else {}
                print(f"[INFO] Webhook response for {conv_id}: {result}")
                
                # Update payload with memory status
                memory_text = result.get("Memory", "")
                status = result.get("Status", "False")
                payload["summary"] = memory_text
                payload["memoryStatus"] = status
                
                # Add to memories
                memories_list.append(payload)
                
                # Mark as processed
                new_conversations[conv_id] = payload
                
            except requests.RequestException as e:
                print(f"[ERROR] Error sending payload for {conv_id}: {e}")
                continue
            except json.JSONDecodeError as e:
                print(f"[ERROR] Error decoding JSON for {conv_id}: {e}")
                continue
        
        # Update processed conversations record
        save_processed_conversations(processed_conversations, new_conversations)
        
        # Update memories file
        save_json_file(MEMORIES_FILE, {"memories": memories_list})
        
        print(f"[INFO] Processing complete at {datetime.now().isoformat()}")
        print(f"[INFO] Processed {len(new_conversations)} new conversations")
        
    except Exception as e:
        print(f"[ERROR] Unexpected error in main processing: {e}")


if __name__ == "__main__":
    main()