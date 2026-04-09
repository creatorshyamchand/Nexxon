from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

COPYRIGHT_STRING = "@nexxonhackers | Developed by CREATOR SHYAMCHAND"

def get_pro_challan_info(rc_number):
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

        # ১. ওনারের নাম খোঁজার স্পেশাল লজিক
        # সাইটে নাম সাধারণত বড় অক্ষরে h2 বা নির্দিষ্ট ডিভে থাকে যা "Owner Name" টেক্সটের উপরে থাকে
        owner_name = "N/A"
        owner_label = soup.find(string=lambda t: t and "Owner Name" in t)
        if owner_label:
            # লেবেলের ঠিক আগের এলিমেন্ট বা উপরের এলিমেন্ট চেক করা
            parent_div = owner_label.find_parent("div")
            if parent_div:
                # নাম সাধারণত h2 বা p ট্যাগে থাকে
                name_tag = parent_div.find_previous_sibling() or parent_div.find("h2") or parent_div.find("p")
                if name_tag:
                    owner_name = name_tag.get_text(strip=True).replace("Owner Name", "")

        # ২. অন্যান্য ডাটা ফিল্টার (Vehicle Info Style)
        def get_data_by_label(label):
            try:
                target = soup.find(string=lambda t: t and label in t)
                if target:
                    parent = target.find_parent("div")
                    # লেবেলের নিচের p ট্যাগ থেকে ডাটা নেওয়া
                    val_tag = parent.find_next_sibling("div") or parent
                    return val_tag.get_text(strip=True).replace(label, "").strip()
                return "N/A"
            except:
                return "N/A"

        vehicle_details = OrderedDict()
        vehicle_details["Owner Name"] = owner_name if owner_name != "N/A" else get_data_by_label("Owner Name")
        vehicle_details["RTO Code"] = get_data_by_label("Code")
        vehicle_details["City"] = get_data_by_label("City Name")
        vehicle_details["Address"] = get_data_by_label("Address")

        # ৩. চালানের লিস্ট স্ক্র্যাপ করা
        challan_list = []
        # সাইটে 'card-body' এর ভেতরে চালানের তথ্য থাকে
        for card in soup.find_all("div", class_="card-body"):
            c_info = {}
            for p in card.find_all("p"):
                txt = p.get_text(strip=True)
                if ":" in txt:
                    k, v = txt.split(":", 1)
                    c_info[k.strip()] = v.strip()
            
            if "Challan Number" in c_info or "Challan No" in c_info:
                challan_list.append(c_info)

        return {
            "status": "success",
            "vehicle_number": rc,
            "data": {
                "owner_info": vehicle_details,
                "challan_details": {
                    "total_challans": len(challan_list),
                    "records": challan_list
                }
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "🚗 Ultimate Vehicle & Challan API is Live",
        "developer": COPYRIGHT_STRING,
        "usage": "/lookup?rc=UP70AJ2399"
    })

@app.route("/lookup", methods=["GET"])
def lookup():
    rc = request.args.get("rc")
    if not rc:
        return jsonify({"error": "RC number required"}), 400

    result = get_pro_challan_info(rc)
    result["credits"] = COPYRIGHT_STRING
    return jsonify(result)

# Vercel handler
app_handler = app
