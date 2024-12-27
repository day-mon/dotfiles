#!/bin/zsh
if hash nvim >> /dev/null 2>&1; then
	alias vi=nvim
	alias v="nvim"
    alias nvimrc='nvim ~/.config/nvim/'
fi


if hash tidy-viewer >> /dev/null 2>&1; then
  alias tv=tidy-viewer
fi
 
if hash pacman >> /dev/null 2>&1; then
	alias update-mirrors="sudo reflector --protocol https --verbose --latest 25 --sort rate --save /etc/pacman.d/mirrorlist && paru -Syyu"
	alias remove-orphans="pacman -Rns $(pacman -Qdtq)"
	alias pac="sudo pacman"

	# get fastest mirrors
	alias mirror="sudo reflector -f 30 -l 30 --number 10 --verbose --save /etc/pacman.d/mirrorlist"
	alias mirrord="sudo reflector --latest 50 --number 20 --sort delay --save /etc/pacman.d/mirrorlist"
	alias mirrors="sudo reflector --latest 50 --number 20 --sort score --save /etc/pacman.d/mirrorlist"
	alias mirrora="sudo reflector --latest 50 --number 20 --sort age --save /etc/pacman.d/mirrorlist"
fi

if hash bat >> /dev/null 2>&1; then
    alias cat="bat"
fi

if hash topgrade >> /dev/null 2>&1; then
    alias update=topgrade
fi

if hash btop >> /dev/null 2>&1; then
    alias top=btop
    alias htop=btop
fi

alias mkdir="mkdir -pv"
alias cd..="cd .."
alias ..="cd .."
alias oports="netstat -tulanp"
alias df="df -h"
alias cpv='rsync -ah --info=progress2'
alias untar="tar -xvf"

alias gl="git log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"
alias rmsym="rm -i"

if hash docker-compose >> /dev/null 2>&1; then
    alias dcd="docker-compose down"
    alias du="docker-compose pull && docker-compose down && docker-compose up -d"
fi

alias zsh-update-plugins="find "$ZDOTDIR/plugins" -type d -exec test -e '{}/.git' ';' -print0 | xargs -I {} -0 git -C {} pull -q"



if hash rg >> /dev/null 2>&1; then
    alias grep=rg
else
    # Colorize grep output (good for log files)
    alias grep='grep --color=auto'
    alias egrep='egrep --color=auto'
    alias fgrep='fgrep --color=auto'
fi
# confirm before overwriting something
alias cp="cp -i"
#if hash rip >> /dev/null 2>&1; then
#  alias rm=rip
#fi
# easier to read disk
alias df='df -h'     # human-readable sizes
alias free='free -m' # show sizes in MB

# get top process eating memory
alias psmem='ps auxf | sort -nr -k 4 | head -5'

# update grub
alias update-grub="sudo grub-mkconfig -o /boot/grub/grub.cfg"

# get signing key
alias get-gpg-sk="gpg --list-keys | awk 'FNR > 3 {print $1; exit}'"

# get top process eating cpu ##
alias pscpu='ps auxf | sort -nr -k 3 | head -5'

if hash eza >> /dev/null 2>&1; then
    alias ls='eza --icons --long --header --git'
    alias l="ls -all"
    alias ll=ls
    alias ln="ls -snew"
else 
    alias ls='ls --color=auto'
    alias ll='ls -lav --ignore=..'   # show long listing of all except ".."
    alias l='ll'   # show long listing but no hidden dotfiles except "."
fi

alias gs='git status'
alias gp='git push'
alias gc='git commit'
alias gd='git diff'
# Auto binds cntrl arrows to back and forward
bindkey "^[[1;5C" forward-word
bindkey "^[[1;5D" backward-word
bindkey -e
