#!/bin/zsh


# if not interactive bail
[[ $- != *i* ]] && return

if [[ $1 == "--debug" ]]; then
    zmodload zsh/zprof
fi


setopt inc_append_history share_history

# Source useful functions (from chris@machine)
source "$ZDOTDIR/functions.zsh"


# Sourced files
# zsh_add_file "zsh-executions"
zsh_add_file "aliases.zsh"

# Plugins
zsh_add_plugin "zsh-users/zsh-autosuggestions"
zsh_add_plugin "zsh-users/zsh-syntax-highlighting"
zsh_add_plugin "hlissner/zsh-autopair"
zsh_add_plugin "bobsoppe/zsh-ssh-agent"
zsh_add_plugin "mafredri/zsh-async"
zsh_add_plugin "romkatv/zsh-defer"
# For more plugins: https://github.com/unixorn/awesome-zsh-plugins

eval "$(starship init zsh)"

add_all_ssh $1

# Colors
autoload -Uz colors && colors
autoload -Uz compinit
[ ! "$(find ~/.config/zsh/.zcompdump -mtime 1)" ] || compinit
compinit -C


if [[ $1 == "--debug" ]]; then
    zprof
fi
