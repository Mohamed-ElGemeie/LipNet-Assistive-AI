from moviepy.editor import VideoFileClip
from os import remove
import os
import pysrt
from string import punctuation
import sys
import re

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

    if((text[0] == "[") and (text[-1] == "]")):
        return False
    
    text = english_to_arabic_numbers(text)
    text = remove_special_char(text)
    text = remove_repeating_spaces(text)
    
    if(check_if_not_arabic(text)):
        return False
    
    if(len(text) < 2):
        return False
        
    if(len(text.split(" ")) <= 1):
        return False

    return text



video_id = sys.argv[1]
sub_id = int(sys.argv[2])

output_video_path = CLIPPED_VIDEOS+ f"/{video_id}_{sub_id}.mp4"
output_alignment_path = CLIPPED_ALIGNMENTS+f"/{video_id}_{sub_id}.align"
input_video_path = DOWNLOADED_VIDEOS +f"/T_{video_id}.mp4"
input_alignment_path = DOWNLOADED_ALIGNMENTS + f"/{video_id}.srt"


def clip():
    try:

        video = VideoFileClip(input_video_path)
        sub = pysrt.open(input_alignment_path)[sub_id]

        text = filter_srt_sub(sub.text.strip())

        if(not text):
            print("False")
            if os.path.exists(output_alignment_path):
                remove(output_alignment_path)

            if os.path.exists(output_video_path):
                remove(output_video_path)
            return

        if os.path.exists(output_alignment_path):
            remove(output_alignment_path)

        with open(output_alignment_path,"w",encoding="utf-8") as writer:
            print(text.replace(" ","\n"))
            writer.write(text.replace(" ","\n"))

        if os.path.exists(output_video_path):
            remove(output_video_path)

        start_time = sub.start.ordinal /1000.0
        end_time = sub.end.ordinal / 1000.0     

        video_part = video.subclip(start_time, end_time)
        video_part.write_videofile(output_video_path,verbose=False, progress_bar=False) 
    
        video.close()
        print('True')
        return

    except Exception as e:
        video.close()

        if os.path.exists(output_alignment_path):
            remove(output_alignment_path)

        if os.path.exists(output_video_path):
            remove(output_video_path)

        print('False')
        return


clip()