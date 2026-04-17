#!/bin/zsh

# Function
function take () {
    mkdir -p $1
    cd $1
}

function sizeofdr() {
    sudo du -sh $1
}

function kill-port() {
    local PID
    PID=$(lsof -i tcp:$1 | awk 'FNR==2{print $2;exit}')

    echo "Port for $PID"

    kill_pid ""$PID""
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
