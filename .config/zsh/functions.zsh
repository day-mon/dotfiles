#!/bin/zsh

# Function
function take () {
    mkdir -p $1
    cd $1
}

function upload() {
  python $HOME/.important/dotfiles/scripts/upload_file.py --token $UPLOAD_TOKEN --files $1
}

function sizeofdr() {
    sudo du -sh $1
}

function gpg-export () {
    gpg --armor --export $1
}

function kill-port() {
    local PID
    PID=$(lsof -i tcp:$1 | awk 'FNR==2{print $2;exit}')

    echo "Port for $PID"

    kill_pid ""$PID"" 
}

function randomchars() {
    openssl rand -base64 $1
}

function prkillro() {
    prkill $1
    $1 & >> /dev/null 2>&1
}

function prkill() {
    local PID
    PID=$(pgrep $1 | awk '{print $1; exit}')
    kill_pid "$PID" $1
}

function change_to_ssh_repo() {
    local REMOTE_URL
    REMOTE_URL=$(git remote get-url origin)

    if [ "$?" -ne 0 ]; then
        echo "Not in a git repo"
        return 1
    fi

    # check if its an ssh url or not
    if [[ "$REMOTE_URL" == git@* ]]; then
        REMOTE_URL=$(echo "$REMOTE_URL" | sed -e "s/https:\/\//git@/g" -e "s/\.com:/\.com:/g")
        git remote set-url origin "$REMOTE_URL"
        printf "SSH URL Check (Swich to SSH)... ${GREEN}OK${NC}\n"
    else
        printf "SSH URL Check (Already set)... ${GREEN}OK${NC}\n"
    fi
}


function drive-uuid() {
    sudo blkid -o value -s UUID $1
}

# Function to source files if they exist
function zsh_add_file() {
    if [ -f "$ZDOTDIR/$1" ]; then
        source "$ZDOTDIR/$1"
    fi
}

function kill_pid() {
    local PID
    PID=$1
    local PNAME
    PNAME=$2

    # Check if the PID is valid
    if [ -z "$PID" ]; then 
        echo "No process found with name $PNAME"
        return
    fi

    # Attempt to kill the process with the SIGTERM signal
    kill -s SIGTERM "$PID"

    if [ $? -eq 0 ]; then
        printf "PID: %d, has been sent the SIGTERM signal :)\n" "$PID"
        
        if ! ps -p $PID > /dev/null 2>&1; then
            printf "PID: %d, has been killed :)\n" "$PID"
            return
        else
           printf "PID: %d could not be killed. Waiting 5 seconds to force kill\n" "$PID" 
        fi
    else
        printf "PID %d, could not be sent the SIGTERM signal :(. Error $?\n" "$PID"
        return
    fi

    # Wait 5 seconds
    sleep 5

    # Check if the process is still alive
    if kill -0 "$PID" 2> /dev/null; then
        # If the process is still alive, kill it with the SIGKILL signal
        kill -s SIGKILL "$PID"

        if [ $? -eq 0 ]; then
            printf "PID: %d, has been killed with the SIGKILL signal :)\n" "$PID"
        else
            printf "PID %d, could not be killed with the SIGKILL signal :(. Error $?\n" "$PID"
            return
        fi
    else
      printf "PID: %d was killed gracefully after 5 seconds" "$PID"
    fi

}



function add_all_ssh() {
  eval `ssh-agent` &>/dev/null

  if [ ! -d "$HOME/.ssh" ]; then
    echo "No .ssh directory found"
    return
  fi

   files=$(ls "$HOME/.ssh" | wc -l)
    if [ "$files" -eq 0 ]; then
      return
    fi

  for key in "${HOME}/.ssh"/*; do
    if [ ! -f "$key" ]; then 
        continue
    fi

    ssh_key=$(head -1 $key)
    if [ "$ssh_key" = "-----BEGIN OPENSSH PRIVATE KEY-----" ]; then
        ssh-add "$key" >> /dev/null 2>&1
        ssh_exit_status=$?
        if [ "$1" = "--debug" ]; then
          :
        elif [ ${ssh_exit_status} -eq 0 ]; then
            echo "Successfully added $key"
        else
            echo "Could not add $key. Error code ${ssh_exit_status}"
        fi
    fi
  done
}

function zsh_add_plugin() {
    PLUGIN_NAME=$(echo $1 | cut -d "/" -f 2)
    if [ -d "$ZDOTDIR/plugins/$PLUGIN_NAME" ]; then 
        # For plugins
        zsh_add_file "plugins/$PLUGIN_NAME/$PLUGIN_NAME.plugin.zsh" || \
        zsh_add_file "plugins/$PLUGIN_NAME/$PLUGIN_NAME.zsh"
    else
        git clone "git@github.com:$1.git" "$ZDOTDIR/plugins/$PLUGIN_NAME"
    fi
}


function zsh_add_theme() {
    THEME_NAME=$(echo $1 | cut -d "/" -f 2)
    if [ -d "$ZDOTDIR/themes/$THEME_NAME" ]; then 
        # For plugins
	echo "${THEME_NAME} has been loaded!"
        zsh_add_file "themes/$THEME_NAME/$THEME_NAME.zsh-theme"
    else
        git clone "git@github.com:$1.git" "$ZDOTDIR/themes/$THEME_NAME"
    fi
}

function zsh_add_completion() {
    PLUGIN_NAME=$(echo $1 | cut -d "/" -f 2)
    if [ -d "$ZDOTDIR/plugins/$PLUGIN_NAME" ]; then 
        # For completions
		completion_file_path=$(ls $ZDOTDIR/plugins/$PLUGIN_NAME/_*)
		fpath+="$(dirname "${completion_file_path}")"
        zsh_add_file "plugins/$PLUGIN_NAME/$PLUGIN_NAME.plugin.zsh"
    else
        git clone "https://github.com/$1.git" "$ZDOTDIR/plugins/$PLUGIN_NAME"
		fpath+=$(ls $ZDOTDIR/plugins/$PLUGIN_NAME/_*)
        [ -f $ZDOTDIR/.zccompdump ] && $ZDOTDIR/.zccompdump
    fi
	completion_file="$(basename "${completion_file_path}")"
	if [ "$2" = true ] && compinit "${completion_file:1}"
}

function mach_java_mode() {
    #THIS MUST BE AT THE END OF THE FILE FOR SDKMAN TO WORK!!!
    export SDKMAN_DIR="$HOME/.sdkman"
    [[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && source "$HOME/.sdkman/bin/sdkman-init.sh"
}

