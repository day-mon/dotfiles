export VISUAL="zed --wait"
eval "$(/opt/homebrew/bin/brew shellenv)"
eval "$($HOME/.local/bin/mise activate zsh)"
export TERM=xterm
source ~/.orbstack/shell/init.zsh 2>/dev/null || :
