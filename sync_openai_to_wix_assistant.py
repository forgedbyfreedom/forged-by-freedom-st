#!/usr/bin/env python3
"""
sync_local_transcripts_to_wix.py
---------------------------------
Uploads all transcript files from the local `transcripts/` folder
to your Wix CMS ("ForgedByFreedom_KB").

Requirements:
  pip install requests
Environment:
  export WIX_API_KEY="..."
  export WIX_SITE_ID="..."
"""

import os
import requests

# ========================
# 🔧 Configuration
# ========================
WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")

if not WIX_API_KEY:
    raise ValueError("❌ Missing WIX_API_KEY.")
if not WIX_SITE_ID:
    raise ValueError("❌ Missing WIX_SITE_ID.")

TRANSCRIPT_DIR = os.path.expanduser("~/forged-by-freedom-st/transcripts")
FAILED_DIR = os.path.join(TRANSCRIPT_DIR, "failed_syncs")

os.makedirs(FAILED_DIR, exist_ok=True)

print(f"📂 Scanning folder: {TRANSCRIPT_DIR}")
if not os.path.isdir(TRANSCRIPT_DIR):
    raise FileNotFoundError(f"❌ Folder not found: {TRANSCRIPT_DIR}")


# ========================
# ⚙️ Helper: upload to Wix
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
        failed_path = os.path.join(FAILED_DIR, f"{filename}.txt")
        with open(failed_path, "w") as f:
            f.write(content)


# ========================
# 🚀 Main Logic
# ========================
txt_files = [f for f in os.listdir(TRANSCRIPT_DIR) if f.endswith(".txt")]
print(f"🧾 Found {len(txt_files)} .txt files to upload.\n")

if not txt_files:
    print("❌ No transcript files found. Exiting.")
    exit(1)

for filename in txt_files:
    file_path = os.path.join(TRANSCRIPT_DIR, filename)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")
        continue

    if not content:
        print(f"⚠️ Skipping empty file: {filename}")
        continue

    push_to_wix(filename, content)

print("\n🎉 Done! All transcripts uploaded to Wix.")
