import sys
from cv2 import VideoCapture,cvtColor, absdiff,COLOR_BGR2RGB,COLOR_BGR2GRAY,CAP_PROP_FPS,CAP_PROP_FRAME_COUNT,CAP_PROP_FRAME_WIDTH,CAP_PROP_FRAME_HEIGHT
from mediapipe.python.solutions.face_mesh import FaceMesh
from mediapipe.python.solutions.face_detection import FaceDetection
from pandas import read_csv, concat,DataFrame
from numpy import mean
from time import sleep
from glob import glob
from shutil import copy, move
import matplotlib.pyplot as plt
from gc import collect
import random
import numpy as np
from math import sqrt

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
CLIPPER = r"scripts/clip_video.py"
FILTERER = r'scripts/filter_videos.py'
RUNTIME = sys.executable.replace('\\','/')

face_mesh = FaceMesh(min_detection_confidence=0)
face_detection = FaceDetection(model_selection=2, min_detection_confidence=0)

video_id = sys.argv[1]
sub_id = int(sys.argv[2])

input_video_path = FILTERED_VIDEOS + f"/{video_id}_{sub_id}.mp4"
input_alignment_path =  CLIPPED_ALIGNMENTS+f"/{video_id}_{sub_id}.align"


def log_status_video(status):
    return
    status_df = read_csv(STATUS_DATASET)
    new_row = {'video_id': f"{video_id}_{sub_id}", 'status': status}
    status_df = concat([status_df, DataFrame([new_row])], ignore_index=True)
    status_df.to_csv(STATUS_DATASET,index=False) 

def check_outliers(numbers,threshold):

    mean = sum(numbers) / len(numbers)
    
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    std_dev = variance ** 0.5
    
    upper_threshold = mean + (threshold * std_dev)
    
    for num in numbers:
        if num > upper_threshold:
            return True
    
    return False

def video_is_accpeted():

    try:
        
        cap = VideoCapture(input_video_path)

        if not cap.isOpened():
            log_status_video(f"Video Don't Open")
            print("False")
            cap.release()
            return

        video_fps = int(cap.get(CAP_PROP_FPS))
        video_frames = int(cap.get(CAP_PROP_FRAME_COUNT))
        video_width = int(cap.get(CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(CAP_PROP_FRAME_HEIGHT))
        video_duration = video_frames // video_fps

        if (video_width * video_height) < (854 * 480):
            log_status_video(f"Bad Resolution {video_width}x{video_height}")
            print("False")
            cap.release()
            return

        if (int(video_duration) < 2) or (int(video_duration) > 5):
            log_status_video(f"Bad Duration {int(video_duration)}")
            print("False")
            cap.release()
            return

        if((video_fps < 25) or (video_fps > 60)):
            log_status_video(f"Bad FPS {video_fps}")
            print("False")
            cap.release()
            return

        # lip coordinates,
        lip_pairs = [[13, 14]]

        # list for whether frames are lips are moving rapidly
        lip_diffs = []
        frame_diffs = []
        orientation_list=[]
        prev_frame = None
        first = True
        prev_lip = None

        # loop over all frames in the video
        for _ in range(int(cap.get(CAP_PROP_FRAME_COUNT))):
            ret, frame = cap.read()

            if not ret:
                continue

            if not first:
                diff = absdiff(prev_frame, frame)

                gray_diff = cvtColor(diff, COLOR_BGR2GRAY)
                avg_diff = mean(gray_diff)
                frame_diffs.append(avg_diff)

            prev_frame = frame.copy()
            first = False

            # convert to rgb
            frame = cvtColor(frame, COLOR_BGR2RGB)

            face_detection_result = face_detection.process(frame)
            face_mesh_result = face_mesh.process(frame)
            

            if face_detection_result.detections == None:
                # log_status_video(f"No Face Detected")
                # print("False")
                # cap.release()
                # return
                continue

            if (len(face_detection_result.detections) !=1):
                log_status_video(f"Bad amount of Faces {len(face_detection_result.detections)}")
                print("False")
                cap.release()
                return
   
            if (not face_mesh_result.multi_face_landmarks):
                # log_status_video(f"No Lips Detected")
                # print("False")
                # cap.release()
                # return
                continue

            for face_landmarks in face_mesh_result.multi_face_landmarks:
            
                landmarks = face_landmarks.landmark
                
                right_x = int(landmarks[454].x * frame.shape[1])
                left_x = int(landmarks[234].x * frame.shape[1])
                upper_x = int(landmarks[10].x * frame.shape[1])
                lower_x = int(landmarks[152].x * frame.shape[1])

                center_x = (upper_x + lower_x)//2

                if ((left_x>center_x) or (right_x<center_x)):
                    orientation_list.append(0)
                else:
                    orientation_list.append(1)

                lip_diff = 0

                for lip_pair in lip_pairs:
                    upper_lip_x, upper_lip_y = int(
                        landmarks[lip_pair[0]].x * frame.shape[1]
                    ), int(landmarks[lip_pair[0]].y * frame.shape[0])
                    lower_lip_x, lower_lip_y = int(
                        landmarks[lip_pair[1]].x * frame.shape[1]
                    ), int(landmarks[lip_pair[1]].y * frame.shape[0])
                    lip_diff += ((upper_lip_x - lower_lip_x) ** 2) + (
                        (upper_lip_y - lower_lip_y) ** 2
                    )

            if prev_lip != None:
                lip_diffs.append(abs(prev_lip-sqrt(lip_diff)))

            prev_lip = float(sqrt(lip_diff))

        if (len(lip_diffs) < int(video_frames*0.8)):
            log_status_video(f"No lips Detected 2")
            print("False")
            cap.release()
            return

        if(len(frame_diffs) < int(video_frames-4)):
            log_status_video(f"No Frame Differences Detected")
            print("False")
            cap.release()
            return

        if (len(orientation_list) < int(video_frames*0.8)):
            log_status_video(f"No Orientation Detected")
            print("False")
            cap.release()
            return
        print(sum(lip_diffs)/len(lip_diffs))
        if( (sum(lip_diffs)/len(lip_diffs)) < 1):
            log_status_video(f"Lips not moving")
            print("False")
            cap.release()
            return

        if(check_outliers(frame_diffs,3)):
            log_status_video(f"Sudden Movment Detected")
            print("False")
            cap.release()
            return

        if ((sum(orientation_list)/len(orientation_list)) < 0.9):
            log_status_video(f"Bad Orientation {sum(orientation_list)/len(orientation_list)}")
            print("False")
            cap.release()
            return
        
        # copy(input_video_path,FILTERED_VIDEOS)
        # copy(input_alignment_path,FILTERED_ALIGNMENTS)
        log_status_video(f"Parsed")
        print("True")
        cap.release()
        return

    except Exception as e:
        log_status_video(f"ERROR {str(e)}")
        print('False')
        cap.release()
        return

video_is_accpeted()