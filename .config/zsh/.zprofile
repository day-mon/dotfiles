export VISUAL="zed --wait"
if [ -x /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi
if [ -x "$HOME/.local/bin/mise" ]; then
    eval "$("$HOME/.local/bin/mise" activate zsh)"
fi
export TERM=xterm
source ~/.orbstack/shell/init.zsh 2>/dev/null || :
