from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

COPYRIGHT_STRING = "@nexxonhackers | Developed by CREATOR SHYAMCHAND"

def get_final_challan_status(rc_number):
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

        # ১. ওনারের নাম খোঁজা (VIVEKANAND PANDEY)
        owner_name = "N/A"
        # সাইটের প্রথম h2 ট্যাগটি সাধারণত নাম হয়
        owner_tag = soup.find("h2")
        if owner_tag:
            owner_name = owner_tag.get_text(strip=True)

        # ২. স্ট্যাটাস বা অভিনন্দন বার্তা খোঁজা (Congratulation! No challan found)
        status_message = ""
        # সাইটের নির্দিষ্ট সাকসেস মেসেজ কন্টেইনার বা টেক্সট খোঁজা
        congrat_div = soup.find(lambda tag: tag.name in ["div", "p", "h4"] and "Congratulation" in tag.text)
        if congrat_div:
            status_message = congrat_div.get_text(strip=True)
        else:
            # যদি সরাসরি না পায় তবে অন্য কোনো নোটিফিকেশন চেক করা
            alert = soup.find("div", class_="alert-success")
            if alert:
                status_message = alert.get_text(strip=True)

        # ৩. অন্যান্য তথ্য (Address, City, RTO)
        def get_v(label):
            try:
                target = soup.find(string=lambda t: t and label in t)
                if target:
                    parent = target.find_parent("div")
                    return parent.get_text(strip=True).replace(label, "").strip()
                return "N/A"
            except:
                return "N/A"

        vehicle_data = OrderedDict()
        vehicle_data["owner_name"] = owner_name
        vehicle_data["city"] = get_v("City Name")
        vehicle_data["address"] = get_v("Address")

        # ৪. চালানের লিস্ট (যদি থাকে)
        challans = []
        for card in soup.find_all("div", class_="card-body"):
            c_info = {}
            for p in card.find_all("p"):
                txt = p.get_text(strip=True)
                if ":" in txt:
                    k, v = txt.split(":", 1)
                    c_info[k.strip()] = v.strip()
            if "Challan Number" in str(c_info):
                challans.append(c_info)

        return {
            "status": "success",
            "vehicle_number": rc,
            "owner_details": vehicle_data,
            "result": {
                "message": status_message if status_message else "No records found.",
                "total_challans": len(challans),
                "records": challans
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route("/lookup", methods=["GET"])
def lookup():
    rc = request.args.get("rc")
    if not rc:
        return jsonify({"error": "Missing ?rc="}), 400

    res = get_final_challan_status(rc)
    res["credits"] = COPYRIGHT_STRING
    return jsonify(res)

# Vercel handler
app_handler = app
