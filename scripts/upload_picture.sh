#!/bin/sh

DATE=$(date '+%h_%Y_%d_%I_%m_%S.png');
LOG_LOCATION="${HOME}/.log/"
LOG_FILE_NAME="${HOME}/.log/flameshot.log"
URL="https://upload.montague.im"
flameshot gui -r > ~/Pictures/"$DATE";

if [ $? -ne 0 ]; then
    notify-send "failed"
    exit
fi

notify-send "${$?}"

if [ ! -f LOG_LOCATION ]; then
    mkdir -p "${LOG_LOCATION}"
fi


if [ ! -e LOG_FILE_NAME ]; then
    touch "${LOG_FILE_NAME}"
fi

source ${HOME}/.config/zsh/secrets

UPLOAD=$(curl -H "Content-Type: multipart/form-data" -H "authorization: "${SCREENSHOT_UPLOAD_AUTH}"" -F file=@"${HOME}"/Pictures/"${DATE}" ${URL}/api/upload | jq '.[]' | jq '.[0]' | sed "s/\"//g")

if [ $? -eq 0  ]; then
    echo "[INFO]: File successfully uploaded on ${DATE} to ${UPLOAD} " >> "${LOG_FILE_NAME}"
    notify-send "Screenshot successfully uploaded to ${UPLOAD}"
    echo "${UPLOAD}" | xsel -ib
else
    echo "[ERROR]: File upload to ${URL} has failed " >> "${LOG_FILE_NAME}"
    notify-send "Screenshot has been failed to upload"
fi
