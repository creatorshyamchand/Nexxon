from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict
import os

app = Flask(__name__)
# Emojis এবং Bengali/Hindi সাপোর্ট করার জন্য
app.config['JSON_AS_ASCII'] = False

COPYRIGHT_STRING = "@nexxonhackers | Developed by CREATOR SHYAMCHAND"

def get_challan_details(rc_number: str) -> dict:
    rc = rc_number.strip().upper()
    # চালানের জন্য সঠিক URL
    url = f"https://vahanx.in/challan-search/{rc}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        "Referer": "https://vahanx.in/challan-search",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # যদি তারা JSON রেসপন্স দেয় তবে সেটা হ্যান্ডেল করা
        if "application/json" in response.headers.get("Content-Type", ""):
            return response.json()
        
        # HTML দিলে সেটা থেকে ডাটা বের করা
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Vahanx এর নতুন সিস্টেমে চালানের তথ্য সাধারণত 'card' ক্লাসের ভেতরে থাকে
        challans = []
        cards = soup.find_all("div", class_="card") # বা তাদের নির্দিষ্ট কার্ড ক্লাস
        
        for card in cards:
            details = OrderedDict()
            ps = card.find_all("p")
            for p in ps:
                text = p.get_text(strip=True)
                if ":" in text:
                    key, val = text.split(":", 1)
                    details[key.strip()] = val.strip()
            if details:
                challans.append(details)
        
        if not challans:
            # যদি সরাসরি টেক্সট পাওয়া না যায়, তবে তাদের স্ক্রিপ্ট ট্যাগ চেক করা (প্যারামিটারে যেটা পাঠিয়েছেন)
            return {"status": "success", "message": "No pending challan found or data format changed.", "challans": []}

        return {"status": "success", "vehicle_number": rc, "challans": challans}

    except Exception as e:
        return {"error": str(e)}

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "🚗 Vehicle Challan API is running!",
        "developer": COPYRIGHT_STRING,
        "usage": "/lookup?rc=UP70AJ2399"
    })

@app.route("/lookup", methods=["GET"])
def lookup_challan():
    rc_number = request.args.get("rc")
    if not rc_number:
        return jsonify({
            "error": "Please provide ?rc= parameter",
            "copyright": COPYRIGHT_STRING
        }), 400

    result = get_challan_details(rc_number)
    
    # ফাইনাল আউটপুটে কপিরাইট যোগ করা
    if isinstance(result, dict):
        result["copyright"] = COPYRIGHT_STRING
    
    return jsonify(result)

# Vercel handler
app_handler = app
