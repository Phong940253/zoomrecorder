@echo off
echo Stopping and removing existing container...
docker stop zoomrec-container
docker rm zoomrec-container

echo Building the Docker image...
docker build -t zoomrec:v1.0.0 .

echo Deploying the new container...
docker run -d -it --name zoomrec-container -p 8000:8000 -p 5901:5901 --security-opt seccomp:unconfined zoomrec:v1.0.0

echo Done!
pause
