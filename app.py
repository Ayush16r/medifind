from flask import Flask, request, jsonify, send_from_directory
import random
import string
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

# ---------------- MongoDB Setup ----------------
MONGO_URI = "mongodb+srv://ayush16r:Ayush16r@healxtrail.nlpleiz.mongodb.net/?retryWrites=true&w=majority&appName=HealXtrail"
client = MongoClient(MONGO_URI)
db = client['medifind']
hospitals_col = db['hospitals']
bookings_col = db['bookings']

# ---------------- Flask Setup ----------------
app = Flask(__name__)
# Get Mongo URI from Render Environment Variables
mongo_uri = os.environ.get("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["healx"]


@app.route('/')
def home():
    return render_template("index.html") 
# ---------------- Helpers ----------------
def generate_booking_id():
    return 'BK' + ''.join(random.choices(string.digits, k=6))

def get_booking_counts():
    """Count bookings per hospital"""
    counts = {}
    for b in bookings_col.find({}):
        hid = b["hospital_id"]
        counts[hid] = counts.get(hid, 0) + 1
    return counts

def calculate_crowd_level(hospital_id, available_beds, wait_time):
    """Calculate dynamic crowd level"""
    counts = get_booking_counts()
    bookings = counts.get(hospital_id, 0)
    available_beds = int(available_beds)
    wait_time = int(wait_time.split()[0])  # '15 min' -> 15

    if bookings == 0:
        return "Empty"
    elif bookings < available_beds // 2 and wait_time < 20:
        return "Low"
    elif bookings < available_beds and wait_time < 40:
        return "Medium"
    else:
        return "High"

def serialize_hospital(h):
    """Convert MongoDB document to JSON-friendly dict"""
    return {
        "id": str(h["_id"]),
        "name": h.get("name", ""),
        "address": h.get("address", ""),
        "location": h.get("location", ""),
        "phone": h.get("phone", ""),
        "rating": h.get("rating", ""),
        "available_beds": h.get("available_beds", ""),
        "distance": h.get("distance", ""),
        "wait_time": h.get("wait_time", ""),
        "crowd_level": calculate_crowd_level(str(h["_id"]), h.get("available_beds", 0), h.get("wait_time", "0 min"))
    }

# ---------------- Routes ----------------
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)  

@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    location = request.args.get("location")
    print("DEBUG: location query param =", location)   # <-- check what you receive
    query = {}
    if location:
        query["location"] = {"$regex": f"^{location}$", "$options": "i"}
    print("DEBUG: Mongo query =", query)  # <-- see the actual query sent
    hospitals = hospitals_col.find(query)
    result = [serialize_hospital(h) for h in hospitals]
    return jsonify(result)




@app.route('/api/hospital/<hospital_id>', methods=['GET'])
def get_hospital(hospital_id):
    try:
        h = hospitals_col.find_one({"_id": ObjectId(hospital_id)})
        if not h:
            return jsonify({"error": "Hospital not found"}), 404
        return jsonify(serialize_hospital(h))
    except:
        return jsonify({"error": "Invalid Hospital ID"}), 400

@app.route('/api/booking', methods=['POST'])
def create_booking():
    booking_data = request.get_json()
    booking_data['booking_id'] = generate_booking_id()
    booking_data['created_at'] = datetime.now().isoformat()
    bookings_col.insert_one(booking_data)
    return jsonify({
        "success": True,
        "booking_id": booking_data['booking_id'],
        "message": "Booking created successfully"
    })

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    bookings = list(bookings_col.find({}))
    for b in bookings:
        b["_id"] = str(b["_id"])
    return jsonify(bookings)

# ---------------- Optional: Auto-add Location ----------------
def add_locations():
    # Map hospital names to their locations
    hospital_locations = {
        "City General Hospital": "Downtown",
        "St. Mary's Medical Center": "Midtown",
        "Community Health Clinic": "Suburbs"
        # Add more as needed
    }
    for name, location in hospital_locations.items():
        hospitals_col.update_one(
            {"name": name},
            {"$set": {"location": location}}
        )
    print("✅ Hospital locations updated!")

# ---------------- Main ----------------
if __name__ == '__main__':
    add_locations()  # automatically update hospitals with location
    print("🏥 MediFind Backend Started with MongoDB + Real-Time Crowd!")
    print("🌐 Server running at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
