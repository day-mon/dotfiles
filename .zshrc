export ZDOTDIR=$HOME/.config/zsh
HISTFILE=~/.zshrc_history
setopt appendhistory

# Source useful functions (from chris@machine)
source "$ZDOTDIR/zsh-functions"

# Colors
autoload -Uz colors && colors

# Sourced files
zsh_add_file "zsh-exports"
zsh_add_file "zsh-aliases"
zsh_add_file "secrets"
zsh_add_file ".p10k.zsh"

# Plugins
zsh_add_plugin "zsh-users/zsh-autosuggestions"
zsh_add_plugin "zsh-users/zsh-syntax-highlighting"
zsh_add_plugin "hlissner/zsh-autopair"
zsh_add_plugin "bobsoppe/zsh-ssh-agent"
# For more plugins: https://github.com/unixorn/awesome-zsh-plugins


# Themes
zsh_add_theme "romkatv/powerlevel10k"

add_all_ssh
