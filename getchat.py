import json
import requests
from datetime import datetime, timedelta
import os

# ----- CONFIGURATION -----
API_KEY = "D12M59S-TCJ416W-NE8QN2N-0PGRQAY"
BASE_URL = "https://app.fixxit.ai/api"
WEBHOOK_URL = "https://tannervoutour1.app.n8n.cloud/webhook-test/ff9d72c1-2364-410a-bbd7-ee9c84a13458"

# Files for persistence:
PROCESSED_FILE = "processed_conversations.json"
MEMORIES_FILE = "conversation_memories.json"

# Time gap threshold (in seconds) to start a new “conversation chunk.”
TIME_GAP_THRESHOLD_SECONDS = 1 * 60  # 1 minute for testing

# Option A: Use file as chat source (for testing)
CHATS_SOURCE_FILE = "chats_response.json"


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
    Retrieves chats from the API endpoint.
    This function mimics your retrieve_chats.py script.
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


def load_processed_data():
    """
    Returns a dict for quick lookup:
        {
          (ws_id, thread_id): {
             "lastProcessedAt": datetime,
             "lastUserAIPair": str,
             "lastChunkConversation": str
          },
          ...
        }
    """
    data = load_json_file(PROCESSED_FILE, {"processed": []})
    processed_map = {}
    for item in data.get("processed", []):
        ws = item["workspaceId"]
        th = item["thread_id"]
        processed_map[(ws, th)] = {
            "lastProcessedAt": parse_date(item.get("lastProcessedAt", "")),
            "lastUserAIPair": item.get("lastUserAIPair", ""),
            "lastChunkConversation": item.get("lastChunkConversation", "")
        }
    return processed_map


def save_processed_data(processed_map):
    """
    Convert processed_map back into the JSON structure and save.
    """
    output = {"processed": []}
    for (ws, th), info in processed_map.items():
        output["processed"].append({
            "workspaceId": ws,
            "thread_id": th,
            "lastProcessedAt": format_date(info["lastProcessedAt"]),
            "lastUserAIPair": info["lastUserAIPair"],
            "lastChunkConversation": info["lastChunkConversation"]
        })
    save_json_file(PROCESSED_FILE, output)


def build_user_ai_string(user_text, assistant_text):
    """Helper to combine a 'user + AI' pair into a single string."""
    user_text = user_text.strip() if user_text else ""
    assistant_text = assistant_text.strip() if assistant_text else ""
    if user_text and assistant_text:
        return f"User: {user_text}\n\nAssistant: {assistant_text}"
    elif user_text:
        return f"User: {user_text}"
    elif assistant_text:
        return f"Assistant: {assistant_text}"
    return ""


def extract_user_ai_from_chat(chat):
    """
    Extract user and assistant text from a single chat item.
    Returns (user_text, assistant_text).
    """
    user_text = (chat.get("prompt") or "").strip()
    raw_assistant = (chat.get("response") or "").strip()
    assistant_text = raw_assistant
    try:
        parsed = json.loads(raw_assistant)
        if "text" in parsed:
            assistant_text = parsed["text"].strip()
    except (json.JSONDecodeError, TypeError):
        pass
    return user_text, assistant_text


def extract_last_two_pairs(chunk):
    """
    Extract the last two user/assistant pairs from a chunk.
    Returns a list of up to two strings, each representing a pair.
    """
    pairs = []
    for msg in chunk:
        u_text, a_text = extract_user_ai_from_chat(msg)
        if u_text or a_text:
            pairs.append(build_user_ai_string(u_text, a_text))
    return pairs[-2:]


def chunk_messages_by_time(messages, gap_seconds=TIME_GAP_THRESHOLD_SECONDS):
    """
    Yield sub-lists (chunks) of messages separated by a gap > gap_seconds.
    """
    if not messages:
        return
    current_chunk = [messages[0]]
    previous_time = parse_date(messages[0].get("createdAt", ""))
    for msg in messages[1:]:
        msg_time = parse_date(msg.get("createdAt", ""))
        if (msg_time - previous_time).total_seconds() > gap_seconds:
            yield current_chunk
            current_chunk = [msg]
        else:
            current_chunk.append(msg)
        previous_time = msg_time
    if current_chunk:
        yield current_chunk


def build_conversation_text_from_chunk(chunk_messages):
    """
    Build a conversation string from the messages in one chunk.
    """
    conversation_lines = []
    for msg in chunk_messages:
        user_text, assistant_text = extract_user_ai_from_chat(msg)
        if user_text:
            conversation_lines.append(f"User: {user_text}")
        if assistant_text:
            conversation_lines.append(f"Assistant: {assistant_text}")
    return "\n\n".join(conversation_lines)


def build_chunk_payload(
    chunk_text,
    workspace_id,
    thread_id,
    workspace_name,
    user_name,
    created_at,
    previous_user_ai,
    previous_chunk_text
):
    """
    Build the payload for a single chunk.
    """
    if not previous_user_ai:
        previous_user_ai = "There is not previous conversation for relevancy check"
    if not previous_chunk_text:
        previous_chunk_text = "There is not previous conversation for relevancy check"

    payload = {
        "conversation":     chunk_text,
        "workspaceID":      workspace_id,
        "threadID":         thread_id,
        "user":             user_name,
        "createdAt":        created_at,
        "workspace":        workspace_name,
        "previousContent":  previous_user_ai,
        "previousChunk":    previous_chunk_text,
        "summary":          ""
    }
    return payload


def main():
    ensure_file_exists(PROCESSED_FILE, {"processed": []})
    ensure_file_exists(MEMORIES_FILE, {"memories": []})

    try:
        chats = fetch_all_chats()
    except Exception as e:
        print("Error fetching chats:", e)
        return
    print(f"Retrieved {len(chats)} chat(s) from API.")

    grouped_chats = group_chats_by_thread(chats)
    processed_map = load_processed_data()
    memories_data = load_json_file(MEMORIES_FILE, {"memories": []})
    memories_list = memories_data.get("memories", [])

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    })

    for key, all_messages in grouped_chats.items():
        ws_id, thread_id = key.split("_", 1)
        # entire WSID+TID conversation
        full_thread_text = build_conversation_text_from_chunk(all_messages)

        if (ws_id, thread_id) not in processed_map:
            processed_map[(ws_id, thread_id)] = {
                "lastProcessedAt": datetime.min,
                "lastUserAIPair": "",
                "lastChunkConversation": ""
            }

        last_processed_dt = processed_map[(ws_id, thread_id)]["lastProcessedAt"]
        last_user_ai     = processed_map[(ws_id, thread_id)]["lastUserAIPair"]
        last_chunk_text  = processed_map[(ws_id, thread_id)]["lastChunkConversation"]

        # only new messages since lastProcessedAt
        new_messages = [
            m for m in all_messages
            if m.get("createdAt", "") == "" or parse_date(m["createdAt"]) > last_processed_dt
        ]
        if not new_messages:
            print(f"[INFO] No new messages for {key} after {last_processed_dt.isoformat()}")
            continue

        first_msg = new_messages[0]
        workspace_name = first_msg.get("workspace", {}).get("name", "Default Workspace")
        user_name      = first_msg.get("user", {}).get("username", "")

        for chunk in chunk_messages_by_time(new_messages, TIME_GAP_THRESHOLD_SECONDS):
            chunk_text       = build_conversation_text_from_chunk(chunk)
            chunk_created_at = chunk[0].get("createdAt", "")

            payload = build_chunk_payload(
                chunk_text=chunk_text,
                workspace_id=ws_id,
                thread_id=thread_id,
                workspace_name=workspace_name,
                user_name=user_name,
                created_at=chunk_created_at,
                # now pass full history into previousContent
                previous_user_ai=full_thread_text,
                previous_chunk_text=last_chunk_text
            )

            print(f"Sending chunk payload for conversation {key} (size={len(chunk)}):")
            print(json.dumps(payload, indent=2))

            try:
                response = session.post(WEBHOOK_URL, json=payload)
                response.raise_for_status()
                result = response.json() if response.text.strip() else {}
                print(f"Webhook response for {key}: {result}")
            except requests.RequestException as e:
                print(f"Error sending payload for {key}: {e}")
                continue
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON for {key}: {e}")
                continue

            memory_text = result.get("Memory", "")
            status      = result.get("Status", "False")
            payload["summary"]      = memory_text
            payload["memoryStatus"] = status
            memories_list.append(payload)

            last_msg_dt = parse_date(chunk[-1].get("createdAt", ""))
            state = processed_map[(ws_id, thread_id)]
            state["lastProcessedAt"]     = last_msg_dt
            state["lastUserAIPair"]      = "\n\n".join(extract_last_two_pairs(chunk))
            state["lastChunkConversation"] = chunk_text
            last_chunk_text = chunk_text

    save_processed_data(processed_map)
    save_json_file(MEMORIES_FILE, {"memories": memories_list})
    print("Processing complete. Updated processed conversations and conversation memories have been saved.")


if __name__ == "__main__":
    ensure_file_exists(PROCESSED_FILE, {"processed": []})
    ensure_file_exists(MEMORIES_FILE, {"memories": []})
    main()

