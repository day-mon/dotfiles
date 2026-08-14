#!/bin/zsh

# Keep Ghostty's title in sync with the current directory without replacing
# hooks installed by Starship or other plugins.
autoload -Uz add-zsh-hook

_set_ghostty_title() {
    [[ $TERM_PROGRAM == ghostty ]] && print -Pn "\e]2;%1~\a"
}

add-zsh-hook precmd _set_ghostty_title
