from fastapi import FastAPI
import subprocess
import os
import time
from pydantic import BaseModel
import socket
import traceback
from concurrent.futures import ThreadPoolExecutor


app = FastAPI()

class ZoomMeeting(BaseModel):
    meeting_link: str
    id: str
    passcode: str
    name: str
    description: str

def check_new_txt_file(directory, known_files):
    while True:
        files = os.listdir(directory)
        new_files = [f for f in files if f.endswith(".txt") and f not in known_files]

        if new_files:
            print('New txt File Found:', new_files)
            # Updating the known_files list
            known_files += new_files
            return new_files[0]
        time.sleep(1)  # wait for 1 second before rechecking the directory

def find_open_port(starting_port):
    port = starting_port
    while True:
        if port_is_open(port):
            return port
        port += 1

def port_is_open(port, host='localhost'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5) # We don't want to wait forever
    # if the process using the port has not yet been closed at the operating system level 
    if not check_port_in_use(port):
        try:
            sock.bind((host, port))
            sock.listen(1)  # Listen for connections
            sock.close()
            return True
        except socket.error:  # If we can't open the port
            return False
    return False

def check_port_in_use(port):
    cmd = "sudo lsof -i :%s" % port
    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    if "LISTEN" in out.decode('utf-8'):
        return True
    else:
        return False
app = FastAPI()

class ZoomMeeting(BaseModel):
    meeting_link: str
    id: str
    passcode: str
    name: str
    description: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/join-meeting")
def join_meeting(zoom_meeting: ZoomMeeting):
    command = f"python3 zoomrec.py -u '{zoom_meeting.meeting_link}' -n '{zoom_meeting.name}' -d '{zoom_meeting.description}' -i '{zoom_meeting.id}' -p '{zoom_meeting.passcode}'"
    process = subprocess.Popen(command, shell=True)
    return {"message": "Meeting started"}
