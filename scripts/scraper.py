from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from pytube import YouTube
import time
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

def create_web_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Initialize the Chrome driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)


    return driver

def create_db_client():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['ArLip']
    return db



driver = create_web_driver()
db = create_db_client()
video_collection = db['videos']
words_collection = db['words']

def get_max_video_id():
    try:
        max_id = video_collection.find().sort("id", -1).limit(1)[0]['id']
    except:
        return -1
    return max_id
    
def get_unscraped_words():

    words = list(words_collection.find({'searched':False}))
    return words

def get_videos_from_words(query,scroll_ahead, word_id):
    url = f"https://www.youtube.com/results?search_query={query}"
    driver.get(url)
    print("Waiting for page to load...")
    time.sleep(3)  # wait for the page to load

    # Scroll and retrieve more video links
    scroll_pause_time = 5  # Time to wait for page to load after each scroll


    last_height = driver.execute_script("return document.documentElement.scrollHeight")

    while True:
        if scroll_ahead > 0:
            print(f"Scrolling at {scroll_ahead}...")
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(scroll_pause_time)  # Wait to load page content
            scroll_ahead -= 1
            last_height = driver.execute_script("return document.documentElement.scrollHeight")
            continue
            
        videos = driver.find_elements(By.XPATH, '//a[@id="video-title"]')
        counter = 30
        for video in reversed(videos):
            video_link = video.get_attribute('href')
             
            if len(list(video_collection.find({"link":video_link}))) > 0:
                print("found duplicate...")
                counter = counter - 1 
                if counter < 0 :
                    print("\n\nfound too many duplicates...\n\n")
                    break
                continue
            try_again = 3
            while(try_again > 0):
                try:
                    
                    yt = YouTube(video_link)

                    # stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

                    if "a.ar" in yt.captions.keys():
                        max_video_id  = get_max_video_id()
                        print("Adding video: ",video_link)
                        sample_video = Video(link=video_link, id=max_video_id + 1,word_id=word_id, status=0)
                        try:
                            video_collection.insert_one(sample_video.model_dump())
                        except:
                            print("found duplicate...")
                    break
                except:
                    print(f"Can't open video at {try_again} try...",)
                    try_again = try_again - 1

        # Scroll down to the bottom of the page
        print("Scrolling...")
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(scroll_pause_time)  # Wait to load page content
        
        new_height = driver.execute_script("return document.documentElement.scrollHeight")

        word_db = words_collection.find_one({"query":query})
        
        if (new_height == last_height) or word_db['scroll_ahead'] > 200:
            print("Searched the word: ",query)
            words_collection.update_one({"query":query},{"$set":{"searched":True}})
            break

        last_height = new_height
        print("Incremented the scroll ahead of word: ",query)
        words_collection.update_one({"query":query},{"$inc":{"scroll_ahead":1}})
    

if __name__ == '__main__':
    words = get_unscraped_words()
    print(len(words)," Unscraped Words\n")
    for word in words:
        if not word['searched']:
            print(f"Searching {word['query']} till page {word['scroll_ahead']} ...\n")
            get_videos_from_words(word['query'],word['scroll_ahead'], word['id'])