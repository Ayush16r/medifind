from flask import Flask, render_template, request, jsonify
import random
import string
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

# ---------------- Flask Setup ----------------
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

# ---------------- MongoDB Setup ----------------
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise Exception("Please set the MONGO_URI environment variable in Render")

# Use a global variable for fork-safe Gunicorn
mongo_client = None
db = None
hospitals_col = None
bookings_col = None

def init_db():
    global mongo_client, db, hospitals_col, bookings_col
    if mongo_client is None:
        mongo_client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False)
        db = mongo_client["medifind"]
        hospitals_col = db["hospitals"]
        bookings_col = db["bookings"]

# ---------------- Helpers ----------------
def generate_booking_id():
    return 'BK' + ''.join(random.choices(string.digits, k=6))

def get_booking_counts():
    init_db()
    counts = {}
    for b in bookings_col.find({}):
        hid = b["hospital_id"]
        counts[hid] = counts.get(hid, 0) + 1
    return counts

def calculate_crowd_level(hospital_id, available_beds, wait_time):
    counts = get_booking_counts()
    bookings = counts.get(hospital_id, 0)
    available_beds = int(available_beds)
    wait_time = int(wait_time.split()[0]) if wait_time else 0

    if bookings == 0:
        return "Empty"
    elif bookings < available_beds // 2 and wait_time < 20:
        return "Low"
    elif bookings < available_beds and wait_time < 40:
        return "Medium"
    else:
        return "High"

def serialize_hospital(h):
    return {
        "id": str(h["_id"]),
        "name": h.get("name", ""),
        "address": h.get("address", ""),
        "location": h.get("location", ""),
        "phone": h.get("phone", ""),
        "rating": h.get("rating", ""),
        "available_beds": h.get("available_beds", 0),
        "distance": h.get("distance", ""),
        "wait_time": h.get("wait_time", "0 min"),
        "crowd_level": calculate_crowd_level(
            str(h["_id"]),
            h.get("available_beds", 0),
            h.get("wait_time", "0 min")
        )
    }

# ---------------- Routes ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/results")
def results():
    return render_template("results.html")

@app.route("/booking")
def booking_page():
    return render_template("booking.html")

@app.route("/confirmation")
def confirmation_page():
    return render_template("confirmation.html")

@app.route("/api/hospitals", methods=["GET"])
def get_hospitals():
    init_db()
    location = request.args.get("location")
    query = {}
    if location:
        query["location"] = {"$regex": f"^{location}$", "$options": "i"}
    try:
        hospitals = list(hospitals_col.find(query))
        return jsonify([serialize_hospital(h) for h in hospitals])
    except Exception as e:
        return jsonify({"error": "Failed to fetch hospitals", "details": str(e)}), 500

@app.route("/api/hospital/<hospital_id>", methods=["GET"])
def get_hospital(hospital_id):
    init_db()
    try:
        h = hospitals_col.find_one({"_id": ObjectId(hospital_id)})
        if not h:
            return jsonify({"error": "Hospital not found"}), 404
        return jsonify(serialize_hospital(h))
    except:
        return jsonify({"error": "Invalid Hospital ID"}), 400

@app.route("/api/booking", methods=["POST"])
def create_booking():
    init_db()
    booking_data = request.get_json()
    booking_data['booking_id'] = generate_booking_id()
    booking_data['created_at'] = datetime.now().isoformat()
    bookings_col.insert_one(booking_data)
    return jsonify({
        "success": True,
        "booking_id": booking_data['booking_id'],
        "message": "Booking created successfully"
    })

@app.route("/api/bookings", methods=["GET"])
def get_bookings():
    init_db()
    bookings = list(bookings_col.find({}))
    for b in bookings:
        b["_id"] = str(b["_id"])
    return jsonify(bookings)

# ---------------- Optional: Auto-add Location ----------------
def add_locations():
    init_db()
    hospital_locations = {
        "City General Hospital": "Downtown",
        "St. Mary's Medical Center": "Midtown",
        "Community Health Clinic": "Suburbs"
    }
    for name, location in hospital_locations.items():
        hospitals_col.update_one({"name": name}, {"$set": {"location": location}})
    print("✅ Hospital locations updated!")

# ---------------- Main ----------------
if __name__ == "__main__":
    add_locations()
    print("🏥 MediFind Backend Started!")
    app.run(debug=True, host="0.0.0.0", port=5000)
