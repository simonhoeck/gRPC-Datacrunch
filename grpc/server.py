#!/usr/bin/env python3
"""
Die Bond Analyzer – Flask backend
Serves the frontend (index.html + JSON files) and provides live MongoDB access.

Usage:
    pip install flask pymongo python-dotenv
    python server.py
    open http://localhost:8080
"""
import os
import json
import datetime
from pathlib import Path

from flask import Flask, jsonify, send_from_directory, make_response
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

MONGO_HOST = os.getenv("MONGO_HOST", "ATRAPC0114")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_USER = os.getenv("MONGO_USER", "admin")
MONGO_PASS = os.getenv("MONGO_PASSWORD", "")
MONGO_DB   = os.getenv("MONGO_DB",   "grpcdata")
PORT       = int(os.getenv("PORT",   "8080"))

MONGO_URI = (
    f"mongodb://{MONGO_USER}:{MONGO_PASS}"
    f"@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
)

COLLECTIONS = [
    "preproduction_reports",
    "creation_reports",
    "transfer_reports",
    "bonding_reports",
    "pbi_reports",
    "alignment_reports",
    "pickup_reports",
]

DATA_DIR = Path(__file__).parent
app = Flask(__name__)


# -- JSON serializer (handles ObjectId + datetime) -----------------------------

class BsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return super().default(obj)


def json_resp(data, status=200):
    resp = make_response(json.dumps(data, cls=BsonEncoder), status)
    resp.headers["Content-Type"] = "application/json"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


# -- MongoDB helper ------------------------------------------------------------

def get_db():
    """Returns a connected MongoDB database handle. Raises on failure."""
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")   # raises ServerSelectionTimeoutError if down
    return client[MONGO_DB]


# -- Routes --------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(DATA_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    """Serve JSON files and any other static assets from the data directory."""
    return send_from_directory(DATA_DIR, filename)


@app.route("/api/status")
def api_status():
    """Check MongoDB connectivity and return document counts per collection."""
    try:
        db = get_db()
        counts = {c: db[c].estimated_document_count() for c in COLLECTIONS}
        return json_resp({
            "connected": True,
            "host":      MONGO_HOST,
            "db":        MONGO_DB,
            "counts":    counts,
        })
    except Exception as exc:
        return json_resp({"connected": False, "error": str(exc)}, 503)


@app.route("/api/counts")
def api_counts():
    """Component counts per production_id — used by the live polling mechanism."""
    try:
        db = get_db()
        result = {}
        pipeline = [{"$group": {"_id": "$production_id", "count": {"$sum": 1}}}]
        for col in COLLECTIONS:
            for doc in db[col].aggregate(pipeline):
                pid = doc["_id"]
                if pid is None:
                    continue
                if pid not in result:
                    result[pid] = {}
                result[pid][col.replace("_reports", "")] = doc["count"]
        for pid in result:
            result[pid]["total"] = sum(result[pid].values())
        return json_resp(result)
    except Exception as exc:
        return json_resp({"error": str(exc)}, 503)


@app.route("/api/<collection>")
def api_collection(collection):
    """Return all documents from a MongoDB collection (excluding _id)."""
    if collection not in COLLECTIONS:
        return json_resp({"error": f"Unknown collection: {collection}"}, 404)
    try:
        db  = get_db()
        docs = list(db[collection].find({}, {"_id": 0}))
        return json_resp(docs)
    except Exception as exc:
        return json_resp({"error": str(exc)}, 503)


@app.route("/api/<collection>/production/<path:pid>")
def api_collection_by_production(collection, pid):
    """Return documents filtered by production_id (faster for large collections)."""
    if collection not in COLLECTIONS:
        return json_resp({"error": f"Unknown collection: {collection}"}, 404)
    try:
        db   = get_db()
        docs = list(db[collection].find({"production_id": pid}, {"_id": 0}))
        return json_resp(docs)
    except Exception as exc:
        return json_resp({"error": str(exc)}, 503)


# -- Entry point ---------------------------------------------------------------

if __name__ == "__main__":
    print(f"\n  Die Bond Analyzer")
    print(f"  {'-' * 38}")
    print(f"  URL      : http://localhost:{PORT}")
    print(f"  MongoDB  : {MONGO_HOST}:{MONGO_PORT}  /  DB: {MONGO_DB}")
    print(f"  Mode     : JSON files  +  live MongoDB API")
    print(f"  {'-' * 38}\n")
    app.run(host="0.0.0.0", port=PORT, debug=False)
