#!/bin/sh

DATE=$(date '+%h_%Y_%d_%I_%m_%S.png');
LOG_LOCATION="${HOME}/.log/"
LOG_FILE_NAME="${HOME}/.log/flameshot.log"
URL="https://upload.montague.im/"
flameshot gui -r > ~/Pictures/"$DATE";

if [ ! -f LOG_LOCATION ]; then
    mkdir -p "${LOG_LOCATION}"
fi


if [ ! -e LOG_FILE_NAME ]; then
    touch "${LOG_FILE_NAME}"
fi


UPLOAD=$(curl -H "Content-Type: multipart/form-data" -H "authorization: ""${SCREENSHOT_UPLOAD_AUTH}"" " -F file=@"${HOME}"/Pictures/"${DATE}" ${URL}api/upload | jq '.[]' | jq '.[0]' | sed "s/\"//g" | xsel -ib)

if [ $? -eq 0  ]; then
    echo "[INFO]: File successfully uploaded on ${DATE} to ${URL} " >> "${LOG_FILE_NAME}"
else 
    echo "[ERROR]: File upload to ${URL} has failed " >> "${LOG_FILE_NAME}"
fi