import os
import requests
from openai import OpenAI

# 🔧 Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")

# 🧩 Setup clients
client = OpenAI(api_key=OPENAI_API_KEY)

# 🔍 Helper: Upload content to Wix Database
def push_to_wix(filename, content):
    url = "https://www.wixapis.com/wix-data/v2/items"
    headers = {
        "Authorization": WIX_API_KEY,
        "wix-site-id": WIX_SITE_ID,
        "Content-Type": "application/json"
    }
    data = {
        "collectionId": "ForgedByFreedom_KB",  # Your Wix Collection
        "item": {
            "title": filename,
            "body": content[:50000]  # Trim if needed for database limits
        }
    }
    r = requests.post(url, json=data, headers=headers)
    if r.status_code == 200:
        print(f"✅ Uploaded {filename} to Wix.")
    else:
        print(f"⚠️ Wix upload failed ({r.status_code}): {r.text}")
        # Fallback: save locally for review
        os.makedirs("failed_syncs", exist_ok=True)
        with open(f"failed_syncs/{filename}.txt", "w") as f:
            f.write(content)


# 🚀 Step 1. Get list of OpenAI files
print("🔍 Listing OpenAI user_data files...")
files = [f for f in client.files.list().data if f.purpose in ["user_data", "fine-tune"]]
print(f"Found {len(files)} file(s).")

if not files:
    print("❌ No accessible files found. Exiting.")
    exit()

# 🚀 Step 2. Create an assistant and attach each file
for f in files:
    print(f"⏳ Reading {f.filename} via Assistant API...")

    try:
        # Create an Assistant
        assistant = client.beta.assistants.create(
            name="Transcript Retriever",
            instructions=f"Return the full contents of the transcript file named {f.filename}.",
            model="gpt-4.1-mini",
            tools=[{"type": "retrieval"}]
        )

        # ✅ Attach file to assistant (new API method)
        client.beta.assistants.files.create(
            assistant_id=assistant.id,
            file_id=f.id
        )

        # Create a thread and run retrieval
        thread = client.beta.threads.create()
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions=f"Retrieve and print the contents of {f.filename}."
        )

        # Wait for completion
        while True:
            status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if status.status == "completed":
                break
            elif status.status == "failed":
                raise Exception("Assistant run failed.")
            else:
                import time
                time.sleep(2)

        # Get response
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        content = messages.data[0].content[0].text.value

        # 🚀 Push to Wix CMS
        push_to_wix(f.filename, content)

    except Exception as e:
        print(f"❌ Error syncing {f.filename}: {e}")

print("\n🎉 Done! All transcripts processed.")
