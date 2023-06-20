ALL_FILES=""$@""

notify-send "📦 Unzipping $ALL_FILES"

if [ -z "$ALL_FILES" ]; then
  return
fi

for f in $ALL_FILES
do
  # get directory up to last slash
  DIR=$(echo "$f" | sed 's/\/[^\/]*$//')

  # unzip into dir
  success=$(unzip -o "$f" -d "$DIR" 2>&1)
  if [ $? -eq 0 ]; then
    notify-send "📦 Unzipped $f"
  else
    notify-send "📦 Unzip failed for $f"
    notify-send "$success"
  fi
done