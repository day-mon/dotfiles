#!/bin/sh

DATE=$(date '+%h_%Y_%d_%I_%m_%S.png');
LOG_LOCATION="${HOME}/.log/"
LOG_FILE_NAME="${HOME}/.log/flameshot.log"
URL="https://upload.montague.im"
PICTURE_PATH="${HOME}/Pictures/${DATE}"
flameshot gui -r > "${PICTURE_PATH}"

if [ $(wc "${PICTURE_PATH}" | awk '{print $1}') -eq 0 ]; then
    rm "${PICTURE_PATH}"
    exit
fi

if [ ! -f LOG_LOCATION ]; then
    mkdir -p "${LOG_LOCATION}"
fi


if [ ! -e LOG_FILE_NAME ]; then
    touch "${LOG_FILE_NAME}"
fi

source ${HOME}/.config/zsh/secrets

UPLOAD=$(curl -H "Content-Type: multipart/form-data" -H "authorization: "${SCREENSHOT_UPLOAD_AUTH}"" -F file=@"${HOME}"/Pictures/"${DATE}" ${URL}/api/upload)

if [ $? -eq 0  ]; then
    UPLOAD=$(jq '.[]' | jq '.[0]' | sed "s/\"//g")
    echo "[INFO]: File successfully uploaded on ${DATE} to ${UPLOAD} " >> "${LOG_FILE_NAME}"
    notify-send "Screenshot successfully uploaded to ${UPLOAD}"
    echo "${UPLOAD}" | xsel -ib
else
    echo "[ERROR]: File upload to ${URL} has failed " >> "${LOG_FILE_NAME}"
    notify-send "Screenshot has been failed to upload"
fi
