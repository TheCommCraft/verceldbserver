from warp.host import TLDServer
from flask import Flask, request
from threading import Thread
import time, requests, secrets

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/about/')
def about():
    return str(tld_server.domains)

domains = {}

tld_server = TLDServer(app=app, tlds=["site", "tcc"], domains=domains)
tld_server.add_domain(domain_name="home.site", key=secrets.randbits(256), owner="warp-project", ip="warp.thecommcraft.de")
tld_server.add_domain(domain_name="home.tcc", key=secrets.randbits(256), owner="thecommcraft", ip="thecommcraft.de")
