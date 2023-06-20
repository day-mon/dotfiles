if hash nemo >> /dev/null 2>&1; then
  nemo
  exit 0
fi

if hash thunar >> /dev/null 2>&1; then
  thunar
  exit 0
fi


notify-send "You dont have thunar or nemo installed. Cannot open thunar/nemo"

