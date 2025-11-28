import os, requests, json, time
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WIX_API_KEY = os.getenv("WIX_API_KEY")
SITE_ID = os.getenv("WIX_SITE_ID")

client = OpenAI(api_key=OPENAI_API_KEY)

# 🔧 Push text to Wix
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
            "body": content[:15000]
        }
    }
    r = requests.post(url, headers=headers, data=json.dumps(data))
    if r.status_code == 200:
        print(f"✅ Uploaded {filename} to Wix ({len(content)} chars)")
    else:
        print(f"⚠️ Wix upload failed ({r.status_code}): {r.text}")

# 🔍 List OpenAI user_data files
print("🔍 Listing OpenAI user_data files...")
files = [f for f in client.files.list().data if f.purpose == "user_data"]
print(f"Found {len(files)} user_data file(s).")

for f in files:
    print(f"⏳ Reading {f.filename} via Assistant API...")

    # 1️⃣ Create assistant
    assistant = client.beta.assistants.create(
        name="Transcript Retriever",
        instructions=f"Read and return the full contents of {f.filename}.",
        model="gpt-4.1-mini",
        tools=[{"type": "retrieval"}]
    )

    # 2️⃣ Attach file
    client.beta.assistants.files.create(
        assistant_id=assistant.id,
        file_id=f.id
    )

    # 3️⃣ Create thread and run
    thread = client.beta.threads.create()
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    # 4️⃣ Retrieve content
    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        content = messages.data[0].content[0].text.value
        push_to_wix(f.filename, content)
    else:
        print(f"⚠️ Failed to process {f.filename} (status: {run.status})")

print("🎉 Sync complete.")
