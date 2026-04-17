# dotfiles

personal dotfiles for zsh, neovim, starship, and friends.

## what's inside

| config | description |
|--------|-------------|
| `zsh` | shell with plugins (autosuggestions, syntax-highlighting, autopair, ssh-agent) |
| `nvim` | neovim with astronvim-based lua config |
| `starship` | minimal shell prompt |
| `ghostty` | terminal emulator config |

## quick setup

```sh
git clone https://github.com/day-mon/dotfiles.git ~/.important/dotfiles
cd ~/.important/dotfiles

# run full setup (installs uv, then symlinks + homebrew packages + fonts + ssh key)
./bootstrap.sh --complete

# or just symlink dotfiles
./bootstrap.sh --setup
```

## setup script options

```sh
uv run scripts/setup.py --help

  --setup      symlink dotfiles to ~/.config
  --ssh        generate ssh key and configure
  --installs   install packages from setup.json
  --upgrade    upgrade existing uv tools
  --complete   do everything
```

## adding packages/fonts

edit `Brewfile` for homebrew packages/fonts, or edit `scripts/setup.json` for uv tools, then re-run:

```sh
uv run scripts/setup.py --installs
```

## requirements

- macos (uses homebrew)
- [uv](https://docs.astral.sh/uv/)
- zsh
