from warp.host import TLDServer
from flask import Flask, request
from threading import Thread
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import time, requests, secrets, os

password = os.getenv("mongodbpw")
uri = f"mongodb+srv://thecommcraft:{password}@cluster0.7xdht5m.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/about/')
def about():
    return str(tld_server.domains)

domains = {}
db = client["db"]
domains = db["domains"]

class DBDict:
    def __init__(self, coll):
        self.coll = coll
    def __getitem__(self, key):
        item = self.coll.find_one({"domain": key})
        if item is None:
            raise KeyError
        return item
    def __setitem__(self, key, value):
        self.coll.replace_one({"domain": key}, value, upsert=True)
    def __contains__(self, key):
        item = self.coll.find_one({"domain": key})
        if item is None:
            return False
        return True
    def get(key, default):
        item = self.coll.find_one({"domain": key})
        if item is None:
            return default
        return item

dbdict = DBDict(domains)

tld_server = TLDServer(app=app, tlds=["site", "tcc"], domains=dbdict)
tld_server.add_domain(domain_name="home.site", key=secrets.tokenurlsafe(32), owner="warp-project", ip="warp.thecommcraft.de")
tld_server.add_domain(domain_name="home.tcc", key=secrets.tokenurlsafe(32), owner="thecommcraft", ip="thecommcraft.de")
