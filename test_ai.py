# test_ai.py
import os
from google import genai

# ⚠️ MAKE SURE THERE ARE NO SPACES AROUND THE KEY
API_KEY = "AIzaSyB6lVvPoMKyYFlg1kWf2fLAO_RVOOK-d48" 

client = genai.Client(api_key=API_KEY)

print("📡 Pinging Google Neural Servers...")
try:
    # Let's try 1.5-flash just to be safe and stable
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents="System Check: Are you online?"
    )
    print(f"✅ SUCCESS: {response.text}")
except Exception as e:
    print(f"❌ FAILED: {str(e)}")