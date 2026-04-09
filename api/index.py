from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

COPYRIGHT_STRING = "@nexxonhackers | Developed by CREATOR SHYAMCHAND"

def get_full_challan_page_info(rc_number):
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

        # ১. নির্দিষ্ট লেবেল ধরে তথ্য খোঁজার ফাংশন (Vehicle Info-এর মতো)
        def get_val(label):
            try:
                # span বা p ট্যাগের ভেতর লেবেলটি খুঁজবে
                target = soup.find(lambda tag: tag.name in ["span", "p", "strong"] and label in tag.text)
                if target:
                    # লেবেলের ঠিক পরের টেক্সট বা প্যারেন্ট ডিভের ভেতরের টেক্সট নেবে
                    parent = target.find_parent("div")
                    if parent:
                        p_text = parent.find("p").get_text(strip=True) if parent.find("p") else parent.get_text(strip=True)
                        return p_text.replace(label, "").strip()
                return "N/A"
            except:
                return "N/A"

        # ২. ওনার এবং লোকেশন ডিটেইলস (OrderedDict দিয়ে সাজানো)
        # যেহেতু সাইটে "VIVEKANAND PANDEY" সরাসরি বড় হেডিংয়ে থাকে, তাই সেটি আলাদাভাবে ধরা হয়েছে
        main_title = soup.find("h2") or soup.find("h1")
        owner_name = main_title.get_text(strip=True) if main_title else get_val("Owner Name")

        data = OrderedDict()
        data["Owner Name"] = owner_name
        data["RTO Code"] = get_val("Code")
        data["City"] = get_val("City Name")
        data["Address"] = get_val("Address")
        data["Phone"] = get_val("Phone")
        data["Website"] = get_val("Website")

        # ৩. চালানের লিস্ট স্ক্র্যাপ করা
        challan_list = []
        challan_cards = soup.find_all("div", class_="card-body")
        
        for card in challan_cards:
            c_info = {}
            lines = card.find_all("p")
            for line in lines:
                text = line.get_text(strip=True)
                if ":" in text:
                    k, v = text.split(":", 1)
                    c_info[k.strip()] = v.strip()
            
            # শুধুমাত্র আসল চালান ডাটা ফিল্টার করা
            if "Challan Number" in str(c_info) or "Amount" in str(c_info):
                challan_list.append(c_info)

        return {
            "status": "success",
            "vehicle_number": rc,
            "vehicle_details": data,
            "challan_info": {
                "total_challans": len(challan_list),
                "challans": challan_list
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "🚗 Pro Challan & Vehicle Info API is Live",
        "developer": COPYRIGHT_STRING,
        "usage": "/lookup?rc=UP70AJ2399"
    })

@app.route("/lookup", methods=["GET"])
def lookup():
    rc = request.args.get("rc")
    if not rc:
        return jsonify({"error": "Please provide ?rc= parameter"}), 400

    result = get_full_challan_page_info(rc)
    result["copyright"] = COPYRIGHT_STRING
    
    return jsonify(result)

# Vercel handler
app_handler = app
