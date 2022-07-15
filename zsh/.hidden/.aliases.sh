# Aliases
alias mkdir="mkdir -pv"
alias v="nvim"
alias cd..="cd .."
alias ..="cd .."
alias vi=nvim
alias oports="netstat -tulanp"
alias df="df -h"
alias cpv='rsync -ah --info=progress2'
alias untar="tar -xvf"
alias pacman="sudo pacman"
alias cat="bat"

# Functions
take () {
    mkdir -p $1
    cd $1
}

randomchars() {
    openssl rand -base64 $1
}
