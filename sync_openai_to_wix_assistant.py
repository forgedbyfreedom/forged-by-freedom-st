#!/usr/bin/env python3
"""
sync_local_transcripts_to_wix.py
---------------------------------
Uploads all transcript files from your local `transcripts/` folder
to your Wix CMS collection (`ForgedByFreedom_KB`).

It automatically checks for duplicates on Wix (by title)
and only uploads new files.

Requirements:
  pip install requests
Environment:
  export WIX_API_KEY="..."
  export WIX_SITE_ID="..."
"""

import os
import requests
import json
from time import sleep

# ========================
# 🔧 Configuration
# ========================
WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")
WIX_COLLECTION_ID = "ForgedByFreedom_KB"

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
# 🧠 Helper: fetch existing Wix titles
# ========================
def get_existing_titles():
    """Fetch all current titles in the Wix collection to avoid duplicates."""
    url = "https://www.wixapis.com/wix-data/v2/items/query"
    headers = {
        "Authorization": WIX_API_KEY,
        "wix-site-id": WIX_SITE_ID,
        "Content-Type": "application/json",
    }

    titles = set()
    skip = 0
    limit = 100

    print("🔍 Fetching existing titles from Wix...")
    while True:
        query = {
            "collectionId": WIX_COLLECTION_ID,
            "dataQuery": {
                "paging": {"limit": limit, "offset": skip},
                "fields": ["title"],
            },
        }

        res = requests.post(url, json=query, headers=headers)
        if res.status_code != 200:
            print(f"⚠️ Failed to fetch titles ({res.status_code}): {res.text}")
            break

        data = res.json()
        items = data.get("items", [])
        if not items:
            break

        for item in items:
            if "title" in item:
                titles.add(item["title"].strip())

        if len(items) < limit:
            break

        skip += limit
        sleep(0.2)

    print(f"✅ Found {len(titles)} existing items on Wix.")
    return titles


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
        "collectionId": WIX_COLLECTION_ID,
        "item": {
            "title": filename,
            "body": content[:50000],
        },
    }

    res = requests.post(url, json=data, headers=headers)

    if res.status_code == 200:
        print(f"✅ Uploaded {filename}")
        return True
    else:
        print(f"⚠️ Upload failed ({res.status_code}): {res.text}")
        failed_path = os.path.join(FAILED_DIR, f"{filename}.txt")
        with open(failed_path, "w") as f:
            f.write(content)
        return False


# ========================
# 🚀 Main Logic
# ========================
existing_titles = get_existing_titles()

txt_files = [
    os.path.join(dp, f)
    for dp, dn, filenames in os.walk(TRANSCRIPT_DIR)
    for f in filenames
    if f.endswith(".txt")
]

print(f"\n🧾 Found {len(txt_files)} local .txt files.\n")

if not txt_files:
    print("❌ No transcript files found. Exiting.")
    exit(1)

uploaded = 0
skipped = 0

for file_path in txt_files:
    filename = os.path.basename(file_path)

    if filename in existing_titles:
        print(f"⏭️ Skipping duplicate: {filename}")
        skipped += 1
        continue

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")
        continue

    if not content:
        print(f"⚠️ Empty file skipped: {filename}")
        continue

    if push_to_wix(filename, content):
        uploaded += 1

print(f"\n🎉 Done! Uploaded {uploaded} new file(s), skipped {skipped} duplicate(s).")
