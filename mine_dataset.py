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
from datetime import datetime
import time
from subprocess import run, Popen,DEVNULL, PIPE, STDOUT
import sys


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

### logging and control functions ###
def empty_dir(dir):
    for i in glob(dir+r"/*"):
        remove(i)

def log(text,log_file):
    try:
        with open(log_file, 'a') as file:
            file.write(text)
    except Exception as e:
        print("Failed to log: ",text, e)

def save_pipeline_status(video_idx,status):
    video_idx_1 =  int(video_idx)
    df = read_csv(LINK_DATASET)
    df["status"][video_idx_1] = status
    df.to_csv(LINK_DATASET,index=False)

def log_status_video(video_id_obj):
    status_df = read_csv(STATUS_DATASET)
    status_df = concat([status_df, DataFrame([video_id_obj])], ignore_index=True)
    status_df.to_csv(STATUS_DATASET,index=False)

def clear_console():
    system('cls' if operating_system_name=='nt' else 'clear')

def serialize_object(obj, name):

    with open(name + '.pickle', 'wb') as f:
        pickle.dump(obj, f)

def check_outliers(numbers,threshold):

    mean = sum(numbers) / len(numbers)

    # Calculate standard deviation
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    std_dev = variance ** 0.5

    # Define thresholds
    upper_threshold = mean + (threshold * std_dev)

    # Check if any number falls outside the thresholds
    for num in numbers:
        if num > upper_threshold:
            return True,upper_threshold  # Return True if any number is outside the thresholds

    return False,upper_threshold  # Return False if no number is outside the thresholds

def calculate_frame_differences(video_path):
    cap = VideoCapture(video_path)
    if not cap.isOpened():
        # print("Error: Couldn't open video file.")
        return None

    # Read the first frame
    ret, prev_frame = cap.read()
    if not ret:
        # print("Error: Couldn't read the first frame.")
        return None

    # Initialize list to store differences
    differences = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Calculate absolute difference between frames
        diff = absdiff(prev_frame, frame)

        # Convert difference image to grayscale
        gray_diff = cvtColor(diff, COLOR_BGR2GRAY)

        # Calculate the average pixel difference
        avg_diff = mean(gray_diff)
        differences.append(avg_diff)

        # Update the previous frame
        prev_frame = frame.copy()
    cap.release()
    # plt.plot(differences);
    return check_outliers(differences,4)

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

def get_video(url, video_id):
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

            return fr"{DOWNLOADED_VIDEOS}/{video_id}.mp4",fr"{DOWNLOADED_ALIGNMENTS}/{video_id} (a.ar).srt"

        else:
            return False, False

    except Exception as e:
        return None,None


DOWNLOADER_THREADS = 0
CLIPPING_SLAVE_THREADS = 20
CLIPPING_THREADS = 10
FILTERING_THREADS = 10
downloader_threads = {}
clipper_threads ={}
filtering_threads = {}
running_clipping = True
running_downloading = False
running_filtering = True

def download_video(url,video_id,status):

    if status != "unparsed" :
        log(f"Skipping video: {video_id} with status {status}\n\n",LOG_FILE_DOWN)
        del downloader_threads[video_id]
        return

    if os.path.exists(fr"{DOWNLOADED_VIDEOS}/R_{video_id}.mp4"):
        log(f"Skipping video: {video_id} as it already exists with status {status}\n\n",LOG_FILE_DOWN)
        save_pipeline_status(video_id,"downloaded")
        del downloader_threads[video_id]
        return

    try:
        result = run([RUNTIME,DOWNLOADER,url,video_id],universal_newlines = True,stdout = PIPE,stderr = STDOUT)

        if "True" in result.stdout:
            rename(fr"{DOWNLOADED_VIDEOS}/{video_id}.mp4",fr"{DOWNLOADED_VIDEOS}/R_{video_id}.mp4")
            log(f"Downloaded: {video_id}\n\n",LOG_FILE_DOWN)
            save_pipeline_status(video_id,"downloaded")
            del downloader_threads[video_id]
            return

        else:
            if os.path.exists(f"{DOWNLOADED_VIDEOS}/{video_id}.mp4"):
                remove(f"{DOWNLOADED_VIDEOS}/{video_id}.mp4")

            log(f"ERROR: {video_id}\n\n",LOG_FILE_DOWN)
            save_pipeline_status(video_id,"failed")
            del downloader_threads[video_id]
            return

    except Exception as e:
        log(f"ERROR: {video_id} {str(e).strip()}\n\n",LOG_FILE_DOWN)
        save_pipeline_status(video_id,"failed")
        del downloader_threads[video_id]
        return

def filter_slave(video_id,sub_id):

    try:

        result = run([RUNTIME,FILTERER ,video_id,sub_id],universal_newlines = True,stdout = PIPE,stderr = STDOUT)

        if "True" in result.stdout:
            rename(CLIPPED_VIDEOS+ f"/T_{video_id}_{sub_id}.mp4",CLIPPED_VIDEOS+ f"/P_{video_id}_{sub_id}.mp4")
            rename(FILTERED_VIDEOS+ f"/T_{video_id}_{sub_id}.mp4",FILTERED_VIDEOS+ f"/{video_id}_{sub_id}.mp4")
            log(f"Filtered video: {video_id}_{sub_id}\n\n",LOG_FILE_CLIP)

        else:
            rename(CLIPPED_VIDEOS+ f"/T_{video_id}_{sub_id}.mp4",CLIPPED_VIDEOS+ f"/X_{video_id}_{sub_id}.mp4")
            log(f"ERROR video: {video_id}_{sub_id}\n\n",LOG_FILE_CLIP)

        del filtering_threads[f"{video_id}_{sub_id}"]
        return

    except:
        del filtering_threads[f"{video_id}_{sub_id}"]
        return

def clip_slave(video_id, sub_id):
    try:

        if os.path.exists(CLIPPED_VIDEOS+ f"/R_{video_id}_{sub_id}.mp4") and os.path.exists(CLIPPED_ALIGNMENTS+f"/{video_id}_{sub_id}.align"):
            log(f"Skipping video: {video_id}_{sub_id}\n\n",LOG_FILE_CLIP)
            return

        result = run([RUNTIME,CLIPPER,video_id,sub_id],universal_newlines = True,stdout = PIPE,stderr = STDOUT)

        if "True" in result.stdout:
            rename(CLIPPED_VIDEOS+ f"/{video_id}_{sub_id}.mp4",CLIPPED_VIDEOS+ f"/R_{video_id}_{sub_id}.mp4")
            log(f"Clipped video: {video_id}_{sub_id}\n\n",LOG_FILE_CLIP)

        else:
            log(f"ERROR video: {video_id}_{sub_id}\n\n",LOG_FILE_CLIP)
        return
    except:
        return

def clip_manager(video_id,_):

    # clipper_slave_threads={}
    length = len(pysrt.open(fr"{DOWNLOADED_ALIGNMENTS}/{video_id}.srt"))
    for sub_id in range(length):
        if not running_clipping:
            del clipper_threads[video_id]
            return
        # while True:

        #     if len(clipper_slave_threads.keys()) < CLIPPING_SLAVE_THREADS:
        #         break

        #     for key, value in clipper_slave_threads.items():
        #         if time.time() - value[1] > 20:
        #             try:
        #                 log(f"ERROR video: {video_id}_{key}\n\n",LOG_FILE_CLIP)
        #                 value[0].join(timeout=1)
        #                 value[0].terminate()
        #                 del clipper_slave_threads[key]
        #             except:
        #                 pass
        clipper_threads[video_id][2] = round((sub_id / length) * 100,3)

        if (os.path.exists(CLIPPED_VIDEOS+ f"/P_{video_id}_{sub_id}.mp4") or os.path.exists(CLIPPED_VIDEOS+ f"/X_{video_id}_{sub_id}.mp4") or os.path.exists(CLIPPED_VIDEOS+ f"/R_{video_id}_{sub_id}.mp4")) and os.path.exists(CLIPPED_ALIGNMENTS+f"/{video_id}_{sub_id}.align"):
            log(f"Skipping video: {video_id}_{sub_id}\n\n",LOG_FILE_CLIP)
            continue
        clip_slave(str(video_id), str(sub_id))


        # thread = threading.Thread(target=clip_slave, args=(, str(sub_id), clipper_slave_threads),daemon=True)
        # clipper_slave_threads[sub_id] = [thread, time.time()]
        # thread.start()
    rename(DOWNLOADED_VIDEOS+f"/T_{video_id}.mp4",DOWNLOADED_VIDEOS+f"/P_{video_id}.mp4")
    save_pipeline_status(video_id,"clipped")
    del clipper_threads[video_id]
    return

def download_controller():

    for idx,row in enumerate(df.values):
        collect()
        if not running_downloading:
            break

        while True:

            if len(downloader_threads.keys()) < DOWNLOADER_THREADS:
                break

            # for key, value in dict(downloader_threads).items():
            #     if time.time() - value[1] > 800:
            #         try:
            #             save_pipeline_status(key,"inquiry")
            #             del downloader_threads[key]
            #         except:
            #             pass

        url = str(row[0])
        video_id = str(row[2])
        status = str(row[4])

        thread = threading.Thread(target=download_video, args=(url,video_id,status),daemon= True)
        downloader_threads[video_id] = [thread,time.time()]
        thread.start()


def clipping_controller():

    while running_clipping:
        for film in glob(DOWNLOADED_VIDEOS+"/R_*.mp4"):
            collect()
            if not running_clipping:
                break

            while True:
                if len(clipper_threads.keys()) < CLIPPING_THREADS:
                    break

            video_id = film.replace("\\","/").split("/")[-1].split(".mp")[0].removeprefix("R_").strip()
            rename(film,DOWNLOADED_VIDEOS+f"/T_{video_id}.mp4")


            thread = threading.Thread(target=clip_manager, args=(str(video_id),"_"),daemon=True)
            clipper_threads[video_id] = [thread,time.time(),0]
            thread.start()


def filtering_controller():

    while running_filtering:

        for clip in glob(CLIPPED_VIDEOS+"/R_*.mp4"):
            collect()
            if not running_filtering:
                break

            while True:
                if len(filtering_threads.keys()) < FILTERING_THREADS:
                    break

            video_id , sub_id= clip.replace("\\","/").split("/")[-1].split(".mp")[0].removeprefix("R_").strip().split("_")

            rename(clip,CLIPPED_VIDEOS+f"/T_{video_id}_{sub_id}.mp4")


            thread = threading.Thread(target=filter_slave, args=(str(video_id),str(sub_id)),daemon=True)
            filtering_threads[f"{video_id}_{sub_id}"] = [thread,time.time()]
            thread.start()

clipper = threading.Thread(target=clipping_controller,daemon=True)
filterer = threading.Thread(target=filtering_controller,daemon=True)

def time_format(seconds):
    hours = seconds // 3600
    remaining_seconds = seconds % 3600
    minutes = remaining_seconds // 60
    remaining_seconds %= 60

    return "{} hours, {} minutes, {} seconds".format(hours, minutes, remaining_seconds)

for process in [clipper,filterer]:
    process.start()



df = read_csv(LINK_DATASET)
df['status'].value_counts()


x = [ y for y in os.listdir(CLIPPED_VIDEOS)]
ready = [y for y in x if y.startswith("R")]
rejected_processed = [y for y in x if (y.startswith("X") or y.startswith("P"))]

clipped_percentage = round((df['status'].value_counts()['clipped'] / (df['status'].value_counts()['clipped'] + df['status'].value_counts()['downloaded'])) * 100,4)
filterted_percentage = round(len(rejected_processed) / (len(ready) + len(rejected_processed))*100,4)
del x
del ready
del rejected_processed

while not ((int(clipped_percentage) == 100) and (int(filterted_percentage) == 100)):

    df = read_csv(LINK_DATASET)

    x = [ y for y in os.listdir(CLIPPED_VIDEOS)]
    ready = [y for y in x if y.startswith("R")]
    rejected_processed = [y for y in x if (y.startswith("X") or y.startswith("P"))]

    clipped_percentage = round((df['status'].value_counts()['clipped'] / (df['status'].value_counts()['clipped'] + df['status'].value_counts()['downloaded'])) * 100,4)
    filterted_percentage = round(len(rejected_processed) / (len(ready) + len(rejected_processed))*100,4)
    del x
    del ready
    del rejected_processed

    print("Percentage of Clipped: ",clipped_percentage)
    print("Percentage of Filtered: ", filterted_percentage)
    print("Amount of captured videos: ",len(os.listdir(FILTERED_VIDEOS)))

    print("Current Clipper Threads: ")
    print("Active threads: ",len(clipper_threads))
    for key,value in clipper_threads.items():
        print(f"{key}: {value[2]}%    -- {time_format(int(time.time()-value[1]))}")

    print("Current Filtering Threads: ")
    print("Active threads: ",len(filtering_threads))
    for key,value in filtering_threads.items():
        print(f"{key}: {time_format(int(time.time()-value[1]))}")


    current_time = datetime.now()
    formatted_time = current_time.strftime("%I:%M %p")
    print("\n\nLast updated at ",formatted_time,"\n\n")
    print("DON'T CLOSE THIS TERMINAL")
    print("DON'T CLOSE Docker Desktop")
    print("DON'T CLOSE THE MACHINE")
    print("DONT' TOUCH OR DISCONNECT THE ORANGE HARD DISK")
    print("please don't do anything without my permission this is my graduation project")
    print("if you have a problem here is my contact information")
    print("\n\n\nMohamed Galal Eldin Elgemeie")
    print("202000206, +201147779310, mgalal2002@outlook.com")
    print("Thank you\n\n")
    sleep(1200)

print("Finished oh yeah")
exit()