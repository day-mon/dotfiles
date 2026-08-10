#!/bin/zsh
set -e

# preexisting uv installs live in ~/.local/bin, which is not on PATH in
# non-interactive shells; make it visible before the existence check so we
# don't reinstall uv every run
export PATH="$HOME/.local/bin:$PATH"

if (( ! $+commands[uv] )); then
    echo "🔧 installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo "🚀 running setup..."
uv run scripts/setup.py "$@"
