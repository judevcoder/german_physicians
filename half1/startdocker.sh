#!/usr/bin/env bash
foldername=${PWD##*/}
docker build -t $foldername .
docker run -i $foldername
thecontainer=`docker ps -l -q`
docker start $thecontainer
docker cp $thecontainer:/usr/src/app/_output .
docker stop $thecontainer
docker rm $thecontainer
docker rmi $foldername