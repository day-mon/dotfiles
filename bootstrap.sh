#!/bin/zsh
set -e

if (( ! $+commands[uv] )); then
    echo "🔧 installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# astral installs into ~/.local/bin, which is not on PATH in non-interactive shells
export PATH="$HOME/.local/bin:$PATH"

echo "🚀 running setup..."
uv run scripts/setup.py "$@"
