export ZDOTDIR=$HOME/.config/zsh
SAVEHIST=1000  # Save most-recent 1000 lines
HISTFILE=${HOME}/.zshrc_history
setopt inc_append_history share_history

# Source useful functions (from chris@machine)
source "$ZDOTDIR/zsh-functions"

# Colors
autoload -Uz colors && colors
autoload -Uz compinit && compinit

# Sourced files
zsh_add_file "zsh-exports"
zsh_add_file "zsh-executions"
zsh_add_file "zsh-aliases"
zsh_add_file "secrets"


# Plugins
zsh_add_plugin "zsh-users/zsh-autosuggestions"
zsh_add_plugin "zsh-users/zsh-syntax-highlighting"
zsh_add_plugin "hlissner/zsh-autopair"
zsh_add_plugin "bobsoppe/zsh-ssh-agent"
# For more plugins: https://github.com/unixorn/awesome-zsh-plugins

eval "$(starship init zsh)"

add_all_ssh


# bun completions
[ -s "/home/damon/.bun/_bun" ] && source "/home/damon/.bun/_bun"
