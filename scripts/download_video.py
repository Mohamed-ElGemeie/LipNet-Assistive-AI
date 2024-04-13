import sys
from pytube import YouTube
from moviepy.editor import VideoFileClip
from moviepy.video.fx.all import crop
from os import path, remove, makedirs, rename,system, name as operating_system_name
import os
from cv2 import VideoCapture,cvtColor, absdiff,COLOR_BGR2RGB,COLOR_BGR2GRAY,CAP_PROP_FPS,CAP_PROP_FRAME_COUNT
from mediapipe.python.solutions.face_mesh import FaceMesh
from mediapipe.python.solutions.face_detection import FaceDetection
from pandas import read_csv, concat,DataFrame
from numpy import mean
from time import sleep
import pysrt
import re 
from string import punctuation
from subprocess import run, Popen
from glob import glob
from shutil import copy, move
from matplotlib.pyplot import plot 
from gc import collect
import threading
import pickle
import datetime
import time
from subprocess import run, Popen,DEVNULL, PIPE, STDOUT


WORK_DIR = r"E:/Video Links Dataset"
CLIPPED_VIDEOS = WORK_DIR + r"/clipped/videos"
CLIPPED_ALIGNMENTS = WORK_DIR + r"/clipped/alignments"
DOWNLOADED_VIDEOS = WORK_DIR + r"/downloaded/videos"
DOWNLOADED_ALIGNMENTS = WORK_DIR + r"/downloaded/alignments"
FILTERED_VIDEOS = WORK_DIR + r"/filtered/videos"
FILTERED_ALIGNMENTS = WORK_DIR + r"/filtered/alignments"
LINK_DATASET = WORK_DIR + r"/Video Links Dataset.csv"
STATUS_DATASET = WORK_DIR + r"/Video Status.csv"
LOG_FILE_DOWN = WORK_DIR + r"/log_down.txt"
LOG_FILE_CLIP = WORK_DIR + r"/log_clip.txt"
LOG_FILE_FILT = WORK_DIR + r"/log_filt.txt"
PICKELS = WORK_DIR + r"/pickles"
DOWNLOADER = r"scripts/download_video.py"
CLIPPER = r"scripts/clip_video.py"
FILTERER = r'scripts/filter_videos.py'
RUNTIME = sys.executable.replace('\\','/')




url = sys.argv[1]
video_id = sys.argv[2]
 

def get_video():
    try:
        yt = YouTube(url)

        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

        if "a.ar" in yt.captions.keys():
            captions = yt.captions.get_by_language_code("a.ar")
            captions.download(
                    srt=True,
                    output_path=DOWNLOADED_ALIGNMENTS,
                    title=f"{video_id}")

            stream.download(
                filename=fr"{DOWNLOADED_VIDEOS}/{video_id}.mp4"
            )

            return True
            # fr"{DOWNLOADED_VIDEOS}/{video_id}.mp4",fr"{DOWNLOADED_ALIGNMENTS}/{video_id} (a.ar).srt"

        else:
            return False
        
    except Exception as e:
        return False

def download_video():

    try:
        fails = 5
        success = False

        while (fails > 0 ) and (success == False):
            success = get_video()
            sleep(2)

        if not success:
            print("False")
            return

        # fix srt file
        run(["go","run",".",fr"{DOWNLOADED_ALIGNMENTS}/{video_id} (a.ar).srt"])
        remove(fr"{DOWNLOADED_ALIGNMENTS}/{video_id} (a.ar).srt")
        rename(fr"{DOWNLOADED_ALIGNMENTS}/{video_id} (a.ar).srt.fixed",fr"{DOWNLOADED_ALIGNMENTS}/{video_id}.srt")
        print("True")
        return
    
    except:
        print("False")
        return
    
thread = threading.Thread(target=download_video, daemon= True)
thread.start()

start_time = time.time()

while thread.is_alive():
    if time.time() - start_time > 3600:
        break
    sleep(60)
