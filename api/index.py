from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# আপনার কাস্টম কপিরাইট
COPYRIGHT_STRING = "@nexxonhackers | Developed by CREATOR SHYAMCHAND"

def get_challan_details(rc_number: str) -> dict:
    rc = rc_number.strip().upper()
    url = f"https://vahanx.in/challan-search/{rc}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        "Referer": "https://vahanx.in/challan-search",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # চালানের লিস্ট খোঁজা
        challan_list = []
        # vahanx সাধারণত কার্ড বা টেবিল ফরম্যাটে চালান দেখায়
        rows = soup.find_all("div", class_="card-body") 

        if not rows:
            return {"status": "no_challan", "message": "No pending challans found or invalid RC."}

        for row in rows:
            details = {}
            # তথ্যের লেবেলগুলো বের করা
            for p in row.find_all("p"):
                text = p.get_text(strip=True)
                if ":" in text:
                    key, val = text.split(":", 1)
                    details[key.strip()] = val.strip()
            
            if details:
                challan_list.append(details)

        return {
            "status": "success",
            "total_challans": len(challan_list),
            "challans": challan_list
        }

    except Exception as e:
        return {"error": f"Failed to fetch data: {str(e)}"}

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "🚦 Vehicle Challan Info API is Live!",
        "developer": "CREATOR SHYAMCHAND",
        "usage": "/challan?rc=WB94P9966"
    })

@app.route("/challan", methods=["GET"])
def challan_lookup():
    rc_number = request.args.get("rc")
    if not rc_number:
        return jsonify({
            "error": "Please provide ?rc= parameter",
            "copyright": COPYRIGHT_STRING
        }), 400

    result = get_challan_details(rc_number)
    
    # রেজাল্টে কপিরাইট যুক্ত করা
    if isinstance(result, dict):
        result["copyright"] = COPYRIGHT_STRING
        result["disclaimer"] = "Data fetched for educational purposes only."
    
    return jsonify(result)

# Vercel app object
app_handler = app
                  
