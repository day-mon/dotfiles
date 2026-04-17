#!/bin/zsh

has() { (( $+commands[$1] )); }

has nvim && {
	alias vi=nvim
	alias v=nvim
	alias nvimrc='nvim ~/.config/nvim/'
}

has tidy-viewer && alias tv=tidy-viewer

has pacman && {
	alias update-mirrors="sudo reflector --protocol https --verbose --latest 25 --sort rate --save /etc/pacman.d/mirrorlist && paru -Syyu"
	alias remove-orphans="pacman -Rns $(pacman -Qdtq)"
	alias pac="sudo pacman"

	# get fastest mirrors
	alias mirror="sudo reflector -f 30 -l 30 --number 10 --verbose --save /etc/pacman.d/mirrorlist"
	alias mirrord="sudo reflector --latest 50 --number 20 --sort delay --save /etc/pacman.d/mirrorlist"
	alias mirrors="sudo reflector --latest 50 --number 20 --sort score --save /etc/pacman.d/mirrorlist"
	alias mirrora="sudo reflector --latest 50 --number 20 --sort age --save /etc/pacman.d/mirrorlist"
}

has bat && alias cat=bat

has topgrade && alias update=topgrade

has btop && {
	alias top=btop
	alias htop=btop
}

alias mkdir="mkdir -pv"
alias cd..="cd .."
alias ..="cd .."
alias oports="netstat -tulanp"
alias df="df -h"
alias cpv='rsync -ah --info=progress2'
alias untar="tar -xvf"

alias gl="git log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"
alias rmsym="rm -i"

has docker-compose && {
	alias dcd="docker-compose down"
	alias du="docker-compose pull && docker-compose down && docker-compose up -d"
}

alias zsh-update-plugins="find "$ZDOTDIR/plugins" -type d -exec test -e '{}/.git' ';' -print0 | xargs -I {} -0 git -C {} pull -q"

has rg && alias grep=rg || {
	alias grep='grep --color=auto'
	alias egrep='egrep --color=auto'
	alias fgrep='fgrep --color=auto'
}

# confirm before overwriting something
alias cp="cp -i"

# easier to read disk
alias df='df -h'     # human-readable sizes
alias free='free -m' # show sizes in MB

# get top process eating memory
alias psmem='ps auxf | sort -nr -k 4 | head -5'

# update grub
alias update-grub="sudo grub-mkconfig -o /boot/grub/grub.cfg"

# get signing key
alias get-gpg-sk="gpg --list-keys | awk 'FNR > 3 {print $1; exit}'"

# get top process eating cpu
alias pscpu='ps auxf | sort -nr -k 3 | head -5'

has eza && {
	alias ls='eza --icons --long --header --git'
	alias l="ls -all"
	alias ll=ls
	alias ln="ls -snew"
} || {
	alias ls='ls --color=auto'
	alias ll='ls -lav --ignore=..'   # show long listing of all except ".."
	alias l='ll'   # show long listing but no hidden dotfiles except "."
}

alias gs='git status'
alias gp='git push'
alias gc='git commit'
alias gd='git diff'

# process killing with uv script
alias killport='uv run ~/.important/dotfiles/scripts/kill.py port'
alias prkill='uv run ~/.important/dotfiles/scripts/kill.py name'
alias prkillro='uv run ~/.important/dotfiles/scripts/kill.py name -r'

# Auto binds cntrl arrows to back and forward
bindkey "^[[1;5C" forward-word
bindkey "^[[1;5D" backward-word
bindkey -e
