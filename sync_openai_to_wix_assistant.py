#!/usr/bin/env python3
"""
sync_openai_to_wix_assistant.py
---------------------------------
Syncs text transcripts stored in OpenAI File Storage (purpose=user_data or fine-tune)
to a Wix CMS Collection ("ForgedByFreedom_KB") using the Assistant API for retrieval.

Requirements:
  pip install openai requests python-dotenv
Environment variables:
  OPENAI_API_KEY
  WIX_API_KEY
  WIX_SITE_ID
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
    raise ValueError("❌ Missing OPENAI_API_KEY in environment.")
if not WIX_API_KEY:
    raise ValueError("❌ Missing WIX_API_KEY in environment.")
if not WIX_SITE_ID:
    raise ValueError("❌ Missing WIX_SITE_ID in environment.")

client = OpenAI(api_key=OPENAI_API_KEY)


# ========================
# ⚙️ Wix Upload Helper
# ========================

def push_to_wix(filename: str, content: str):
    """Uploads extracted content to Wix CMS."""
    url = "https://www.wixapis.com/wix-data/v2/items"
    headers = {
        "Authorization": WIX_API_KEY,
        "wix-site-id": WIX_SITE_ID,
        "Content-Type": "application/json"
    }
    data = {
        "collectionId": "ForgedByFreedom_KB",  # Your Wix collection name
        "item": {
            "title": filename,
            "body": content[:50000]  # Trim if over 50k chars
        }
    }

    print(f"⬆️ Uploading {filename} to Wix...")
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        print(f"✅ Uploaded {filename} successfully.")
    else:
        print(f"⚠️ Wix upload failed ({response.status_code}): {response.text}")
        os.makedirs("failed_syncs", exist_ok=True)
        with open(f"failed_syncs/{filename}.txt", "w") as f:
            f.write(content)


# ========================
# 🚀 Sync Logic
# ========================

print("🔍 Listing OpenAI user_data and fine-tune files...")
files = [f for f in client.files.list().data if f.purpose in ["user_data", "fine-tune"]]
print(f"📁 Found {len(files)} file(s).")

if not files:
    print("❌ No eligible files found in OpenAI storage.")
    exit(1)

for f in files:
    print(f"\n⏳ Processing {f.filename} ({f.id})...")

    try:
        # 🧠 Create Assistant
        assistant =

