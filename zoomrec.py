import subprocess
from datetime import datetime
import time
import random
from openai import OpenAI
from pydub import AudioSegment
from dotenv import load_dotenv
import os
import time
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

client = OpenAI(
  api_key=os.getenv('API_KEY'),  # this is also the default, it can be omitted
)
ended = False


    
def locate(image_path, confidence=0.8):
    """
    Locates an image on the screen.

    Args:
        image_path (str): The path to the image to locate.
        confidence (float): The confidence level for image recognition (default: 0.8).
    """
    import pyautogui
    try:
        x, y = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
        return True, x, y
    except Exception as e:
        return False, 0, 0
    
def locate_and_click(image_path, confidence=0.8, wait=False):
    """
    Locates an image on the screen and clicks its center.

    Args:
        image_path (str): The path to the image to locate.
        confidence (float): The confidence level for image recognition (default: 0.8).
    """
    import pyautogui
    try:
        x, y = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
        if wait:
            time.sleep(random.uniform(1, 2))
        pyautogui.click(x, y)
        return True
    except Exception as e:
        return False
    
def join_meeting(name):
    import pyautogui
    while True:
        if locate_and_click("./img/leave.png"):
            print("Admitted")
            break

        if locate_and_click("./img/join.png", wait=True):
            print("Clicked on Join")
            continue

        if (
            locate_and_click("./img/name_field_check.png")
            or locate_and_click("./img/name_field_check_1.png")
            or locate_and_click("./img/name_field_check_2.png")
        ):
            print("Clicked on Name Field")
            time.sleep(random.uniform(1, 2))
            pyautogui.write(name, interval=0.2)
            locate_and_click("./img/join.png", wait=True)
            continue

        if check_invalid_meeting():
            print("Invalid Meeting Link Provided")
            return False

        time.sleep(0.3)
            
    print("Joined the meeting, Recording now...")

    return True

def check_invalid_meeting():
    return locate_and_click("./img/invalid_meeting_id.png")
    
def record_audio(filename):
    proc = subprocess.Popen(
        [
            "ffmpeg",
            "-y",
            "-f",
            "pulse",
            "-i",
            "ZoomRec.monitor",
            "-acodec",
            "libmp3lame",
            "-b:a",
            "128k",
            "-async",
            "1",
            "-vn",
            f"/home/zoomrec/recordings/{filename}",
        ],
    )

    check_meeting_ended()

    proc.terminate()
    proc.wait()
    
    print("Recording Ended")

def check_meeting_ended():
    global ended
    import pyautogui
    while True:
        if ended:
            print("Meeting Ended")
            break
        try:
            pyautogui.locateCenterOnScreen("./img/end.png", confidence=0.8)
            ended = True
            print("Meeting Ended")
            return True
        except Exception as e:
            print("Meeting is still in progress")
            time.sleep(1)

def record_meeting(name, description):
    is_joined = join_meeting(name)
    if is_joined:
        # audio_name = f"{description if description else 'zoom'}_{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        audio_name = "zoom_recording"
        with ThreadPoolExecutor() as executor:
            executor.submit(record_audio, f"{audio_name}.mp3")
        return audio_name
    else:
        return 0
    
def transcribe_meeting(audio_name):
    while True:
        if os.path.exists(f"/home/zoomrec/recordings/{audio_name}.mp3"):
            print(f'File {audio_name}.mp3 has been found!')
            audio_file = AudioSegment.from_mp3(f"/home/zoomrec/recordings/{audio_name}.mp3")
            audio_length =  len(audio_file)
            print(audio_length)
            transcription = ''
            ten_minutes= 600 * 1000

            for last_snippet_time_stamp in range(0, audio_length, ten_minutes):
                snippet = audio_file[last_snippet_time_stamp: ten_minutes]
                snippet.export("audio_snippet.mp3", format="mp3")
                snippet_transcription = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=open("audio_snippet.mp3", "rb"), 
                        response_format="text"
                    )
                transcription = transcription + snippet_transcription

            print(transcription)

            #Optional
            with open(f"/home/zoomrec/recordings/{audio_name}.txt", "w") as file:
                file.write(transcription)
            break  # Exit the loop
        else:
            print(f'Waiting for the file {audio_name}.mp3...')
            time.sleep(1)  # Wait for 1 second and check again

# Setting logging
from loguru import logger
import sys

logfile = "./logs/run.log"
logger.add(logfile, format="{message}", level="INFO")

class StreamToLogger:
    def __init__(self, level="INFO"):
        self.level = level

    def write(self, message):
        if message.rstrip() != "":
            logger.opt(depth=1).log(self.level, message.rstrip())

    def flush(self):
        pass

sys.stdout = StreamToLogger(level="INFO")


if __name__ == "__main__":
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    import os

    os.environ["PULSE_SINK"] = "ZoomRec"

    if not os.path.exists("/home/zoomrec/recordings"):
        os.mkdir("/home/zoomrec/recordings")

    if not os.path.exists("/home/zoomrec/logs"):
        os.mkdir("/home/zoomrec/logs")

    import argparse

    parser = argparse.ArgumentParser(
        description="Script to receive command line parameters"
    )

    parser.add_argument("-u", "--url", type=str, help="Meeting URL")
    parser.add_argument("-i", "--id", type=str, help="Meeting ID")
    parser.add_argument("-p", "--passcode", type=str, help="Meeting Passcode")
    parser.add_argument("-n", "--name", type=str, help="Display Name", required=True)
    parser.add_argument("-d", "--description", type=str, help="Description")

    args = parser.parse_args()
    
    # kill the zoom process if it is running
    os.system("pkill zoom")

    if args.url:
        url = args.url
        print(url)
        zoom = subprocess.Popen(f'zoom --url="{url}"', stdout=subprocess.DEVNULL, stderr = subprocess.DEVNULL,
                                shell=True, preexec_fn=os.setsid)
    else:
        id = args.id
        passcode = args.passcode
        print(id, passcode)
        zoom = subprocess.Popen(f'zoom --url="zoommtg://zoom.us/join?confno={id}&pwd={passcode}"', stdout=subprocess.DEVNULL, stderr = subprocess.DEVNULL,
                                shell=True, preexec_fn=os.setsid)

    name = args.name
    print("bot name: ", name)
    description = args.description

    time.sleep(random.uniform(3, 5))

    audio_name = record_meeting(name, description)
    # if audio_name != 0:
    #     with ThreadPoolExecutor() as executor:
    #         executor.submit(transcribe_meeting, audio_name)
    # print(audio_name)
