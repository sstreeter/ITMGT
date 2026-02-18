import sqlite3
import os
from flask import Flask, request, jsonify
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration
DB_FILE = os.environ.get('SBS_DB_FILE', '/srv/sbs_inventory/inventory.db')
API_KEY = os.environ.get('SBS_API_KEY')

if not API_KEY:
    print("WARNING: SBS_API_KEY is not set. The server will reject all requests.")


def init_db():
    """Initialize the database schema if it doesn't exist."""
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                uuid TEXT PRIMARY KEY,
                asset_id TEXT,
                serial_number TEXT,
                hostname TEXT,
                model TEXT,
                processor TEXT,
                ram_gb REAL,
                disk_gb REAL,
                mfg_year TEXT,
                ownership_unit TEXT,
                location_building TEXT,
                location_room TEXT,
                location_verified BOOLEAN,
                in_tanium BOOLEAN,
                last_seen TEXT,
                status TEXT,
                agent_version TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error initializing DB: {e}")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def check_api_key():
    """Ensure the request has a valid API key."""
    # Allow simple health check or home without key if needed, but for checkin we need it
    if request.endpoint == 'checkin':
        key = request.headers.get('X-API-Key')
        if key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401

@app.route('/checkin', methods=['POST'])
def checkin():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    uuid = data.get('UUID')
    if not uuid:
        return jsonify({"error": "UUID is required"}), 400

    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if exists
        c.execute('SELECT uuid FROM inventory WHERE uuid = ?', (uuid,))
        exists = c.fetchone()

        # Extract fields
        asset_id = data.get('AssetID')
        serial = data.get('SerialNumber')
        hostname = data.get('Hostname')
        model = data.get('Model')
        processor = data.get('Processor')
        ram = data.get('RAM_GB')
        disk = data.get('Disk_GB')
        mfg = data.get('MfgYear')
        owner = data.get('OwnershipUnit')
        bldg = data.get('LocationBuilding')
        room = data.get('LocationRoom')
        verified = data.get('LocationVerified')
        tanium = data.get('InTanium')
        last_seen = data.get('LastSeen') or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = data.get('Status')
        agent_ver = data.get('AgentVersion')

        if exists:
            # Update
            c.execute('''
                UPDATE inventory SET
                    asset_id = ?, serial_number = ?, hostname = ?, model = ?,
                    processor = ?, ram_gb = ?, disk_gb = ?, mfg_year = ?,
                    ownership_unit = ?, location_building = ?, location_room = ?,
                    location_verified = ?, in_tanium = ?, last_seen = ?, status = ?,
                    agent_version = ?
                WHERE uuid = ?
            ''', (
                asset_id, serial, hostname, model, processor, ram, disk, mfg,
                owner, bldg, room, verified, tanium, last_seen, status, agent_ver, uuid
            ))
            msg = f"Asset {uuid} updated."
        else:
            # Insert
            c.execute('''
                INSERT INTO inventory (
                    uuid, asset_id, serial_number, hostname, model,
                    processor, ram_gb, disk_gb, mfg_year,
                    ownership_unit, location_building, location_room,
                    location_verified, in_tanium, last_seen, status, agent_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                uuid, asset_id, serial, hostname, model, processor, ram, disk, mfg,
                owner, bldg, room, verified, tanium, last_seen, status, agent_ver
            ))
            msg = f"Asset {uuid} registered."
            
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": msg, "AssetID": asset_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    # In production, this should be handled by a WSGI server
    # For dev/testing:
    app.run(host='0.0.0.0', port=5000)