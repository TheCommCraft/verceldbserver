from warp.host import TLDServer
from flask import Flask, request, jsonify
from threading import Thread
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from hmac import compare_digest
import time, requests, secrets, os

password = os.getenv("mongodbpw")
access_key = os.getenv("accesskey") # ah yes
uri = f"mongodb+srv://thecommcraft:{password}@cluster0.7xdht5m.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
app = Flask(__name__)

@app.get('/')
def home():
    return 'Hello, World!'

@app.get('/about/')
def about():
    return str(tld_server.domains)

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
