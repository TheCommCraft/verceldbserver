from warp.host import TLDServer
from flask import Flask, request, jsonify, make_response
from threading import Thread
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from hmac import compare_digest
import time, requests, secrets, os, datetime, json

password = os.getenv("mongodbpw")
access_key = os.getenv("accesskey") # ah yes
uri = f"mongodb+srv://thecommcraft:{password}@cluster0.7xdht5m.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
app = Flask(__name__)

@app.get('/')
def home():
    return 'Hello, World!'

@app.post('/new_domain/<domain_name>/')
def new_domain(domain_name):
    data = request.json
    key = data.get("access_key")
    owner = data.get("owner")
    if not compare_digest(key, access_key):
        return jsonify({"success": False, "reason": "Unauthorized", "key": None})
    if domain_name in dbdict:
        return jsonify({"success": False, "reason": "Already exists", "key": None})
    if not owner:
        return jsonify({"success": False, "reason": "Needs an owner", "key": None})
    key = secrets.token_urlsafe(32)
    tld_server.add_domain(domain_name=domain_name, key=key, owner=owner)
    return jsonify({"success": True, "reason": "Added", "key": key})
    
domains = {}
db = client["db"]
domains = db["domains"]
keys = db["keys"]
kvstore = db["kvstore"]

class DBDict:
    def __init__(self, coll):
        self.coll = coll
        self.data = {}
    def __getitem__(self, key):
        item = self.get(key)
        if item is None:
            raise KeyError
        return item
    def __setitem__(self, key, value):
        value = value.copy()
        value["domain"] = key
        self.data[key] = value
        self.coll.replace_one({"domain": key}, value, upsert=True)
    def __contains__(self, key):
        item = self.get(key)
        if item is None:
            return False
        return True
    def get(self, key, default=None):
        item = self.data.get(key) or self.coll.find_one({"domain": key})
        self.data[key] = item
        if item is None:
            return default
        return item

dbdict = DBDict(domains)
tld_server = TLDServer(app=app, tlds=["site", "tcc"], domains=dbdict)

@tld_server.on("set_domain_ip")
def on_set_ip(event):
    dbdict.coll.update_one({"domain": event.domain_name}, {"$set": {"ip": event.ip}})

@app.route("/wowlele/", methods=["GET", "POST"])
def wowlele():
    keys.insert_one({"data": request.get_data(as_text=True), "headers": json.dumps(dict(request.headers)), "cookies": json.dumps(dict(request.cookies)), "time": datetime.datetime.now()})
    return ""


def set_key_value(key, value):
    kvstore.update_one({"key": key}, {"$set": {"value": value}}, upsert=True)

def get_key_value(key):
    result = kvstore.find_one({"key": key})
    return result["value"] if result else None

@app.post("/storage/file/<file>/")
def submit_file(file):
    data = request.get_data(as_text=True)
    if file != "highscores":
        response = make_response("n", 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    if file == "highscores":
        last_val = get_key_value(file) or ""
        highscores = [(line.split(",", 1)[0], int(line.split(",", 1)[1])) for line in last_val.split(";") if line.strip()]
        new_highscores = sorted([(line.split(",", 1)[0], int(line.split(",", 1)[1])) for line in data.split(";") if line.strip()], key=lambda x: x[1])
        if len(highscores) != len(new_highscores) - 1 and len(highscores) != len(new_highscores) == 10:
            response = make_response("n", 200)
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        diff = set(new_highscores) - set(highscores)
        if len(diff) != 1:
            response = make_response("n", 200)
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        modified_highscores = highscores + list(diff)
        modified_highscores = sorted(modified_highscores, key=lambda x: x[1])[:10]
        if new_highscores != modified_highscores:
            response = make_response("n", 200)
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
    set_key_value(file, data)
    response = make_response("y", 200)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.get("/storage/file/<file>/")
def get_file(file):
    if file != "highscores":
        response = make_response("", 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    response = make_response(get_key_value(file) or "", 200)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route("/storage/file/<file>/", methods=["OPTIONS"])
def file_options(file):
    
    response = make_response()
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response
