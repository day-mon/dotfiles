#!/usr/bin/zsh
PYTHON_PATH=$(which python)
if [ -z $PYTHON_PATH ]; then
  PYTHON_PATH=$(which python3)
  if [ -z $PYTHON_PATH ]; then
    notify-send "❌ Please install python or python3"
    exit
  fi
fi

source "$HOME"/.config/zsh/secrets

if [ -z $UPLOAD_TOKEN ]; then
  notify-send "❌ Please set the UPLOAD_TOKEN variable in $HOME/.config/zsh/secrets"
  exit
fi

# run command with python script
sh -c "$PYTHON_PATH $HOME/.config/zsh/scripts/upload_file.py $@"
