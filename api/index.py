from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Professional Credits
COPYRIGHT_STRING = "@nexxonhackers | Developed by CREATOR SHYAMCHAND"

def fetch_comprehensive_data(rc_number):
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

        # ১. গাড়ির বেসিক তথ্য স্ক্র্যাপ করা (মালিকের নাম, আরটিও ইত্যাদি)
        vehicle_meta = OrderedDict()
        
        # vahanx সাধারণত h1, h2 বা নির্দিষ্ট p ট্যাগে নাম দেখায়
        name_tag = soup.find("h2") or soup.find("h1")
        vehicle_meta["owner_name"] = name_tag.get_text(strip=True) if name_tag else "Not Found"

        # অন্যান্য তথ্য খুঁজে বের করা (City, Address, Website)
        for div in soup.find_all("div", class_="col-md-6"):
            p_tags = div.find_all("p")
            for p in p_tags:
                text = p.get_text(strip=True)
                # লেবেল অনুযায়ী ডাটা ফিল্টার
                if "Code" in text: vehicle_meta["rto_code"] = text.replace("Code", "").strip()
                if "City Name" in text: vehicle_meta["city"] = text.replace("City Name", "").strip()
                if "Address" in text: vehicle_meta["address"] = text.replace("Address", "").strip()

        # ২. চালানের তথ্য স্ক্র্যাপ করা
        challan_list = []
        # সাধারণত টেবিল বা লিস্টে চালান থাকে
        challan_cards = soup.find_all("div", class_="card-body")
        
        for card in challan_cards:
            c_data = {}
            for p in card.find_all("p"):
                line = p.get_text(strip=True)
                if ":" in line:
                    k, v = line.split(":", 1)
                    c_data[k.strip().lower().replace(" ", "_")] = v.strip()
            if c_data and "challan_number" in str(c_data): # নিশ্চিত হওয়া এটি চালানের ডাটা
                challan_list.append(c_data)

        # ৩. ফাইনাল রেসপন্স তৈরি
        return {
            "status": "success",
            "vehicle_number": rc,
            "owner_details": vehicle_meta,
            "challan_summary": {
                "total_challans": len(challan_list),
                "status": "No Pending Challan" if len(challan_list) == 0 else "Challans Found"
            },
            "challans": challan_list
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "api_name": "Pro Vehicle & Challan Tracker",
        "developer": COPYRIGHT_STRING,
        "usage": "/lookup?rc=UP70AJ2399"
    })

@app.route("/lookup", methods=["GET"])
def lookup():
    rc = request.args.get("rc")
    if not rc:
        return jsonify({"error": "RC number is required"}), 400

    result = fetch_comprehensive_data(rc)
    result["credits"] = COPYRIGHT_STRING
    
    return jsonify(result)

# Vercel Handler
app_handler = app
