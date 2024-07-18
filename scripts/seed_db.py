from pymongo import MongoClient
import os
import sys

def load_root_path():
    file_dir = os.path.abspath(__file__)
    lv1_dir = os.path.dirname(file_dir)
    root_dir = os.path.dirname(lv1_dir)
    sys.path.append(root_dir)


load_root_path()

from models.videos import *

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
client.drop_database('ArLip')

db = client["ArLip"]

# MongoDB collections
videos_collection = db.videos
clips_collection = db.clips
words_collection = db.words

# Create indexes on link and id fields to ensure they are unique and indexed for optimization
videos_collection.create_index([("link", 1)], unique=True)
videos_collection.create_index([("id", 1)], unique=True)

words_collection.create_index([("query", 1)], unique=True)
words_collection.create_index([("id", 1)], unique=True)

clips_collection.create_index([("link", 1)], unique=True)
clips_collection.create_index([("id", 1)], unique=True)

# Create objects with incremental ids
video1 = Video(link="http://example.com/video1", id=0, word_id=0, status=0)
clip1 = Clip(link="http://example.com/clip1", id=0, word_id=0, video_id=0)
word1 = Word(id=0,query="A7A", searched=False,scroll_ahead=0)

# Insert objects into MongoDB
videos_collection.insert_one(video1.model_dump())
clips_collection.insert_one(clip1.model_dump())
words_collection.insert_one(word1.model_dump())

# Delete objects (uncomment if needed)
videos_collection.delete_one({"link": "http://example.com/video1"})
clips_collection.delete_one({"link": "http://example.com/clip1"})
words_collection.delete_one({"query": "A7A"})

print("Objects created and db seeded!")
