ALL_FILES=""$@""
URL="https://upload.montague.im"


. "$HOME"/.config/zsh/secrets

if [ -z UPLOAD_TOKEN ]; then
    notify-send "❌ Please set the UPLOAD_TOKEN variable in $HOME/.config/zsh/secrets"
    exit
fi

for f in $ALL_FILES
do
  UPLOAD=$(curl -H "Content-Type: multipart/form-data" -H "authorization: ""${UPLOAD_TOKEN}""" -F file="$f" ${URL}/api/upload)
  if [ $? -eq 0  ]; then
    UPLOAD=$(echo $UPLOAD | jq '.files[0]' | sed "s/\"//g")
    notify-send "✅ Screenshot successfully uploaded to ${UPLOAD}"
else
    notify-send "❌ Screenshot has been failed to upload"
fi
done