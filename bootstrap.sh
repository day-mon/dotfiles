#!/bin/zsh
set -e

if (( ! $+commands[uv] )); then
    echo "🔧 installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo "🚀 running setup..."
uv run scripts/setup.py "$@"
