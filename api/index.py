from warp.host import TLDServer
from flask import Flask, request
from threading import Thread
import time, requests

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/about/')
def about():
    return f'About'

domains = {}

tld_server = TLDServer(app=app, tlds=["site"], domains=domains)
