from pytube import YouTube
from moviepy.editor import VideoFileClip
from moviepy.video.fx.all import crop
from os import path, remove, makedirs, rename
from cv2 import VideoCapture,cvtColor, absdiff,COLOR_BGR2RGB,COLOR_BGR2GRAY,CAP_PROP_FPS,CAP_PROP_FRAME_COUNT
from mediapipe.python.solutions.face_mesh import FaceMesh
from mediapipe.python.solutions.face_detection import FaceDetection
from pandas import read_csv, concat,DataFrame
from numpy import mean
from time import sleep
import pysrt
import re 
from string import punctuation
from subprocess import run
from glob import glob
from shutil import copy, move
from matplotlib.pyplot import plot 
from gc import collect
import threading


WORK_DIR = r"E:/Video Links Dataset"
CLIPPED_VIDEOS = WORK_DIR + r"/clipped/videos"
CLIPPED_ALIGNMENTS = WORK_DIR + r"/clipped/alignments"
DOWNLOADED_VIDEOS = WORK_DIR + r"/downloaded/videos"
DOWNLOADED_ALIGNMENTS = WORK_DIR + r"/downloaded/alignments"
FILTERED_VIDEOS = WORK_DIR + r"/filtered/videos"
FILTERED_ALIGNMENTS = WORK_DIR + r"/filtered/alignments"
LINK_DATASET = WORK_DIR + r"/Video Links Dataset.csv"
STATUS_DATASET = WORK_DIR + r"/Video Status.csv"
LOG_FILE = WORK_DIR + r"/log.txt"

def check_outliers(numbers,threshold):
    if not numbers:
        return False  

    mean = sum(numbers) / len(numbers)
    
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    std_dev = variance ** 0.5
    upper_threshold = mean + (threshold * std_dev)
    
    for num in numbers:
        if num > upper_threshold:
            return True  
    return False  

def calculate_frame_differences(video_path):
    cap = VideoCapture(video_path)
    if not cap.isOpened():
        return False
    

    ret, prev_frame = cap.read()
    if not ret:
        return False
    
    differences = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        diff = absdiff(prev_frame, frame)
        
        gray_diff = cvtColor(diff, COLOR_BGR2GRAY)
        
        avg_diff = mean(gray_diff)
        differences.append(avg_diff)
        
        prev_frame = frame.copy()
    cap.release()
    return(check_outliers(differences,4))

def english_to_arabic_numbers(text):

    numbers_dict = {
        '0': '٠',
        '1': '١',
        '2': '٢',
        '3': '٣',
        '4': '٤',
        '5': '٥',
        '6': '٦',
        '7': '٧',
        '8': '٨',
        '9': '٩',
    }
    for eng_num, arabic_num in numbers_dict.items():
        text = text.replace(eng_num, arabic_num)
    return text

def remove_special_char(text):
    for i in punctuation:
        text = text.replace(i, " ")

    return text

def remove_repeating_spaces(text):
    cleaned_text = re.sub(r' +', ' ', text)
    return cleaned_text

def check_if_not_arabic(text):
    ar = "ابتثجحخدذرزسشصضطظعغفقكلمنهويىء٠١٢٣٤٥٦٧٨٩ "
    for i in text:
        if i not in ar:
            return True
    return False
    
def filter_srt_sub(text):

    if(len(text) < 2):
        return False

    if(text == "[موسيقى]"):
        return False
    
    text = english_to_arabic_numbers(text)
    text = remove_special_char(text)
    text = remove_repeating_spaces(text)
    
    if(check_if_not_arabic(text)):
        return False
    
    if(len(text) < 2):
        return False
    
    return text

import sys


video_id = sys.argv[1]
sub_id = sys.argv[2]

output_video_path = CLIPPED_VIDEOS+ f"/{video_id}_{idx}.mp4"
output_alignment_path = CLIPPED_ALIGNMENTS+f"/{video_id}_{idx}.align"
input_video_path = DOWNLOADED_VIDEOS +f"/T_{video_id}.mp4"
output_alignment_path = 

try:
    sub = pysrt.open(alignment_path)
    video = VideoFileClip(video_path)
    text = filter_srt_sub(sub.text.strip())

    if(not text):
        return

    start_time = sub.start.ordinal /1000.0
    end_time = sub.end.ordinal / 1000.0     

    video_part = video.subclip(start_time, end_time)

    with open(output_alignment_path,"w") as writer:
        writer.write(text.replace(" ","\n"))

    video_part.write_videofile(output_video_path,verbose=False, progress_bar=False) 
    threaded_videos.append(int(idx))

except:
    video.close()
    pass

    video.close()
    remove(output_alignment_path)
    remove(output_video_path)
    del thread_bank[idx]
    return

    video.close()
    del thread_bank[idx]
    return

