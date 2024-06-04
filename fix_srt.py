import time
import re
import sys

class Subtitle:
    def __init__(self, idx, fromTime, toTime, text):
        self.idx = idx
        self.fromTime = fromTime
        self.toTime = toTime
        self.text = text

timeFramePattern = re.compile(r'(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)')

def getDuration(parts):
    hour = int(parts[0])
    minute = int(parts[1])
    second = int(parts[2])
    millisecond = int(parts[3])
    return (time.Millisecond * millisecond) + (time.Second * second) + (time.Minute * minute) + (time.Hour * hour)

def printDuration(duration):
    hour = duration // time.Hour
    duration -= hour * time.Hour
    minute = duration // time.Minute
    duration -= minute * time.Minute
    second = duration // time.Second
    duration -= second * time.Second
    millisecond = duration // time.Millisecond
    return f'{hour:02d}:{minute:02d}:{second:02d},{millisecond:03d}'

def readOneSubtitle():
    idxRaw = input()
    if not idxRaw:
        return None, None
    idx = int(idxRaw)
    timing = timeFramePattern.findall(input())
    if not timing:
        return None, 'invalid subtitle timing'
    fromTime = getDuration(timing[0][0:4])
    toTime = getDuration(timing[0][4:8])
    content = input()
    while True:
        line = input()
        if not line:
            break
        content += '\n' + line
    subtitle = Subtitle(idx, fromTime, toTime, content)
    return subtitle, None

def writeOneSubtitle(subtitle, idx):
    sys.stdout.write(f'{idx}\n')
    sys.stdout.write(f'{printDuration(subtitle.fromTime)} --> {printDuration(subtitle.toTime)}\n')
    sys.stdout.write(f'{subtitle.text}\n\n')
    idx += 1
    return idx

def main():
    idx = 1
    while True:
        subtitle, err = readOneSubtitle()
        if err:
            sys.stderr.write(f'Error: {err}\n')
            break
        if not subtitle:
            break
        idx = writeOneSubtitle(subtitle, idx)

import os
import time
import string
import codecs

def readOneSubtitle(scanner):
    subtitle = {}
    subtitle['fromTime'] = None
    subtitle['toTime'] = None
    subtitle['text'] = ''
    for line in scanner:
        line = line.strip()
        if line == '':
            break
        if subtitle['fromTime'] is None:
            times = line.split(' --> ')
            print(times[0])
            subtitle['fromTime'] = time.strptime(times[0], '%H:%M:%S,%f')
            subtitle['toTime'] = time.strptime(times[1], '%H:%M:%S,%f')
        else:
            subtitle['text'] += line + '\n'
    if subtitle['fromTime'] is None:
        return None
    return subtitle

def writeOneSubtitle(newFile, subtitle, newIdx):
    newFile.write(str(newIdx) + '\n')
    newFile.write(time.strftime('%H:%M:%S,%f', subtitle['fromTime']) + ' --> ' + time.strftime('%H:%M:%S,%f', subtitle['toTime']) + '\n')
    newFile.write(subtitle['text'] + '\n')

def main():
    if len(sys.argv) < 2:
        print("Provide a subtitle file to fix.\ne.g. subtitle-fixer mysubtitle.srt")
        return
    filePath = sys.argv[1]
    newFilePath = filePath + ".fixed"
    file = codecs.open(filePath, 'r', 'utf-8')
    newFile = codecs.open(newFilePath, 'w', 'utf-8')
    scanner = file.readlines()
    newIdx = 1
    lastSubtitle = None
    for line in scanner:
        print(line)
        subtitle = readOneSubtitle(line)
        if lastSubtitle is not None:
            if subtitle is not None:
                subtitle['text'] = subtitle['text'].strip()
                if len(subtitle['text']) == 0:
                    continue
                if subtitle['toTime'] - subtitle['fromTime'] < time.timedelta(milliseconds=150) and subtitle['text'] in lastSubtitle['text']:
                    lastSubtitle['toTime'] = subtitle['toTime']
                    continue
                currentLines = subtitle['text'].split('\n')
                lastLines = lastSubtitle['text'].split('\n')
                if currentLines[0] == lastLines[-1]:
                    subtitle['text'] = '\n'.join(currentLines[1:])
                if subtitle['fromTime'] < lastSubtitle['toTime']:
                    lastSubtitle['toTime'] = subtitle['fromTime'] - time.timedelta(milliseconds=1)
            writeOneSubtitle(newFile, lastSubtitle, newIdx)
        if subtitle is None:
            break
        lastSubtitle = subtitle
    file.close()
    newFile.close()
    # os.rename(filePath, filePath + ".bak")
    os.rename(newFilePath, filePath+".new")

if __name__ == "__main__":
    main()
