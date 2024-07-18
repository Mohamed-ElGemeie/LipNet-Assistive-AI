from flask import Flask, render_template, request, jsonify
import json
from pymongo import MongoClient
import os
import sys

def load_root_path():
    file_dir = os.path.abspath(__file__)
    lv1_dir = os.path.dirname(file_dir)
    root_dir = os.path.dirname(lv1_dir)
    sys.path.append(root_dir)

def create_db_client():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['ArLip']
    return db

load_root_path()

from models.videos import *

app = Flask(__name__,template_folder='../templates')


db = create_db_client()
video_collection = db['videos']

videos =[ i['link'] for i in list(video_collection.find({'status':0}))]

@app.route('/')
def index():
    return render_template(r'collect.html', videos=videos)

@app.route('/accept_video', methods=['POST'])
def accept_video():
    data = request.get_json()
    video_url = data['video_url']
    video_collection.update_one({"link":video_url},{"$set":{"status":1}})
    print(f"Accepted video: {video_url}")
    return jsonify({"status": "success"})

@app.route('/reject_video', methods=['POST'])
def reject_video():
    data = request.get_json()
    video_url = data['video_url']
    video_collection.find_one_and_delete({"link":video_url})
    print(f"deleted video: {video_url}")
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
