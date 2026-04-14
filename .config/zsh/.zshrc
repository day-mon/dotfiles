#!/bin/zsh


# if not interactive bail
[[ $- != *i* ]] && return

if [[ $1 == "--debug" ]]; then
    zmodload zsh/zprof
fi


setopt inc_append_history share_history

source "$ZDOTDIR/functions.zsh"

zsh_add_file "aliases.zsh"

# Plugins
zsh_add_plugin "zsh-users/zsh-autosuggestions"
zsh_add_plugin "zsh-users/zsh-syntax-highlighting"
zsh_add_plugin "hlissner/zsh-autopair"
zsh_add_plugin "bobsoppe/zsh-ssh-agent"
zsh_add_plugin "mafredri/zsh-async"
zsh_add_plugin "romkatv/zsh-defer"
eval "$(starship init zsh)"

# Colors
autoload -Uz colors && colors
autoload -Uz compinit
[ ! "$(find ~/.config/zsh/.zcompdump -mtime 1)" ] || compinit
compinit -C


if [[ $1 == "--debug" ]]; then
    zprof
fi
