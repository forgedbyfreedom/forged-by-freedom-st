# sync_openai_to_wix_assistant.py
import os, requests, json
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WIX_API_KEY = os.getenv("WIX_API_KEY")
SITE_ID = os.getenv("WIX_SITE_ID")

client = OpenAI(api_key=OPENAI_API_KEY)

# 🔧 Helper: push text to Wix collection
def push_to_wix(filename, content):
    url = "https://www.wixapis.com/wix-data/v2/items"
    headers = {
        "Authorization": WIX_API_KEY,
        "wix-site-id": SITE_ID,
        "Content-Type": "application/json"
    }
    data = {
        "collectionId": "ForgedByFreedom_KB",
        "item": {
            "title": filename,
            "body": content[:15000]  # truncate safely
        }
    }
    r = requests.post(url, headers=headers, data=json.dumps(data))
    r.raise_for_status()
    print(f"✅ Uploaded {filename} to Wix ({len(content)} chars)")

# 🔍 Find recent user_data files
print("🔍 Listing OpenAI user_data files...")
files = [f for f in client.files.list().data if f.purpose == "user_data"]
print(f"Found {len(files)} user_data file(s).")

# 🔁 Loop and read via assistant retrieval
for f in files[:3]:  # limit for test
    print(f"⏳ Reading {f.filename} via Assistant API...")

    assistant = client.beta.assistants.create(
        name="Transcript Retriever",
        instructions=f"Read and return the full text contents of {f.filename}.",
        model="gpt-4.1-mini",
        tools=[{"type": "retrieval"}],
        file_ids=[f.id]
    )

    thread = client.beta.threads.create()
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        content = messages.data[0].content[0].text.value
        push_to_wix(f.filename, content)
    else:
        print(f"⚠️ Failed to read {f.filename} (status: {run.status})")

print("🎉 Sync complete.")
