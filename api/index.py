from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Professional Credits
COPYRIGHT_STRING = "@nexxonhackers | Developed by CREATOR SHYAMCHAND"

def get_clean_vehicle_data(rc_number):
    rc = rc_number.strip().upper()
    url = f"https://vahanx.in/challan-search/{rc}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://vahanx.in/challan-search",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # ১. সঠিক ওনার নেম বের করা (Header থেকে)
        # vahanx-এ গাড়ির নাম্বার এর ঠিক নিচেই বড় করে নাম থাকে। 
        # আমরা h2 ট্যাগটি নেব এবং নিশ্চিত করব যেন সেটি 'eChallan' না হয়।
        owner_name = "N/A"
        headers_found = soup.find_all(['h2', 'h1', 'h3'])
        for h in headers_found:
            text = h.get_text(strip=True)
            if text and "eChallan" not in text and rc not in text and "Congratulation" not in text:
                owner_name = text
                break

        # ২. নির্দিষ্ট লেবেল ধরে আরটিও এবং অ্যাড্রেস বের করা
        def find_by_label(label_text):
            try:
                # এমন p বা span খোঁজা যেখানে লেবেলটি আছে
                label_node = soup.find(lambda tag: tag.name in ['p', 'span', 'b'] and label_text in tag.text)
                if label_node:
                    # লেবেলের প্যারেন্ট ডিভ থেকে পুরো টেক্সট নিয়ে লেবেলটি বাদ দেওয়া
                    full_text = label_node.find_parent().get_text(strip=True)
                    return full_text.replace(label_text, "").strip()
                return "N/A"
            except:
                return "N/A"

        # ৩. চালানের মেসেজ হ্যান্ডলিং
        # বিজ্ঞাপন বা ইনস্যুরেন্সের টেক্সট বাদ দিয়ে শুধুমাত্র আসল মেসেজটি নেওয়া
        raw_msg = "No records found."
        msg_box = soup.find("div", class_="alert-success") or soup.find(lambda tag: "Congratulation" in tag.text)
        if msg_box:
            # শুধুমাত্র প্রথম লাইন বা নির্দিষ্ট অংশটুকু নেওয়া (বিজ্ঞাপন বাদে)
            raw_msg = msg_box.get_text(" ", strip=True).split("Car Insurance")[0].split("Bike Insurance")[0].strip()

        # ৪. চালানের লিস্ট (যদি থাকে)
        challans = []
        # সাধারণত কার্ড বডির ভেতর লুপ আকারে থাকে
        cards = soup.find_all("div", class_="card-body")
        for card in cards:
            c_info = {}
            ps = card.find_all("p")
            for p in ps:
                t = p.get_text(strip=True)
                if ":" in t:
                    key, val = t.split(":", 1)
                    c_info[key.strip()] = val.strip()
            
            if "Challan Number" in c_info:
                challans.append(c_info)

        # রেজাল্ট সাজানো
        return {
            "status": "success",
            "vehicle_number": rc,
            "owner_info": {
                "owner_name": owner_name,
                "rto_code": find_by_label("Code"),
                "city": find_by_label("City Name"),
                "address": find_by_label("Address")
            },
            "challan_status": {
                "message": raw_msg,
                "total": len(challans),
                "list": challans
            }
        }

    except Exception as e:
        return {"status": "error", "message": "Server Busy or Invalid RC"}

@app.route("/lookup", methods=["GET"])
def lookup():
    rc = request.args.get("rc")
    if not rc:
        return jsonify({"error": "Missing RC number"}), 400

    data = get_clean_vehicle_data(rc)
    data["credits"] = COPYRIGHT_STRING
    return jsonify(data)

@app.route("/")
def home():
    return jsonify({"status": "Online", "api": "Pro Vehicle Tracker"})

# Vercel handler
app_handler = app
