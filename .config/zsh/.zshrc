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
# Cached tool init — avoids ~80ms of subprocess spawns per shell.
# Regenerate after upgrading a tool: `regen-zsh-cache` (defined in functions.zsh)
zsh_add_file "cache/starship.zsh"
zsh_add_file "cache/mise.zsh"

zsh_add_file "ghostty.zsh"


# Colors
autoload -Uz colors && colors
fpath=(/opt/homebrew/share/zsh/site-functions $fpath)
autoload -Uz compinit

if [[ ! -f ~/.config/zsh/.zcompdump ]] || [[ $(find ~/.config/zsh/.zcompdump -mtime +1 2>/dev/null) ]]; then
    compinit
else
    compinit -C  # use cached dump
fi


if [[ $1 == "--debug" ]]; then
    zprof
fi

# sentry
fpath=("/Users/dmontague/.local/share/zsh/site-functions" $fpath)
