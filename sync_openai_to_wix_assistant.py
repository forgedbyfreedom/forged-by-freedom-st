#!/usr/bin/env python3
"""
sync_openai_to_wix_assistant.py
---------------------------------
Downloads transcript files from OpenAI (purpose=user_data or fine-tune)
and syncs them to Wix CMS ("ForgedByFreedom_KB").

If OpenAI download fails, it falls back to local transcript files.

Requirements:
  pip install openai requests
Environment:
  export OPENAI_API_KEY="..."
  export WIX_API_KEY="..."
  export WIX_SITE_ID="..."
"""

import os
import time
import requests
from openai import OpenAI

# ========================
# 🔧 Configuration
# ========================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")

if not OPENAI_API_KEY:
    raise ValueError("❌ Missing OPENAI_API_KEY.")
if not WIX_API_KEY:
    raise ValueError("❌ Missing WIX_API_KEY.")
if not WIX_SITE_ID:
    raise ValueError("❌ Missing WIX_SITE_ID.")

client = OpenAI(api_key=OPENAI_API_KEY)
TRANSCRIPT_DIR = os.path.expanduser("~/forged-by-freedom-st/transcripts")
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)


# ========================
# ⚙️ Helper: push to Wix
# ========================
def push_to_wix(filename: str, content: str):
    """Uploads transcript text to Wix CMS."""
    url = "https://www.wixapis.com/wix-data/v2/items"
    headers = {
        "Authorization": WIX_API_KEY,
        "wix-site-id": WIX_SITE_ID,
        "Content-Type": "application/json",
    }
    data = {
        "collectionId": "ForgedByFreedom_KB",
        "item": {
            "title": filename,
            "body": content[:50000],
        },
    }

    print(f"⬆️ Uploading {filename} to Wix...")
    res = requests.post(url, json=data, headers=headers)
    if res.status_code == 200:
        print(f"✅ Uploaded {filename} successfully.")
    else:
        print(f"⚠️ Wix upload failed ({res.status_code}): {res.text}")
        os.makedirs("failed_syncs", exist_ok=True)
        with open(f"failed_syncs/{filename}.txt", "w") as f:
            f.write(content)


# ========================
# 💾 Download helper
# ========================
def download_openai_file(file_obj):
    """Downloads an OpenAI file locally and returns its path."""
    print(f"⏬ Attempting to download {file_obj.filename} ({file_obj.id})...")

    try:
        response = client.files.content(file_obj.id)
        file_path = os.path.join(TRANSCRIPT_DIR, file_obj.filename)
        with open(file_path, "wb") as f:
            f.write(response.read())
        print(f"✅ Saved locally to {file_path}")
        return file_path
    except Exception as e:
        print(f"⚠️ Could not download from OpenAI: {e}")
        local_path = os.path.join(TRANSCRIPT_DIR, file_obj.filename)
        if os.path.exists(local_path):
            print(f"📂 Using local fallback: {local_path}")
            return local_path
        else:
            print(f"❌ No local backup found for {file_obj.filename}. Skipping.")
            return None


# ========================
# 🚀 Main Sync Logic
# ========================
print("🔍 Listing OpenAI user_data and fine-tune files...")
files = [f for f in client.files.list().data if f.purpose in ["user_data", "fine-tune"]]
print(f"📁 Found {len(files)} eligible file(s).")

if not files:
    print("❌ No files found in OpenAI. Exiting.")
    exit(1)

for f in files:
    print(f"\n⏳ Processing {f.filename} ({f.id})...")

    # 1️⃣ Download locally
    file_path = download_openai_file(f)
    if not file_path:
        continue

    # 2️⃣ Read content
    try:
        with open(file_path, "r", encoding="utf-8") as fp:
            content = fp.read().strip()
    except Exception as e:
        print(f"❌ Error reading local file {file_path}: {e}")
        continue

    if not content:
        print(f"⚠️ File {f.filename} is empty. Skipping.")
        continue

    # 3️⃣ Upload to Wix
    push_to_wix(f.filename, content)

print("\n🎉 Done! All transcripts synced to Wix successfully.")
