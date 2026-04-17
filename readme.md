# dotfiles

personal dotfiles for zsh, neovim, starship, and friends.

## what's inside

| config | description |
|--------|-------------|
| `zsh` | shell with plugins (autosuggestions, syntax-highlighting, autopair, ssh-agent) |
| `nvim` | neovim with astronvim-based lua config |
| `starship` | minimal shell prompt |
| `ghostty` | terminal emulator config |
| `rofi` | app launcher + powermenu (linux only) |

## quick setup

```sh
git clone https://github.com/day-mon/dotfiles.git ~/.important/dotfiles
cd ~/.important/dotfiles

# run full setup (symlinks + homebrew packages + fonts + ssh key)
python scripts/setup.py --complete

# or just symlink dotfiles
python scripts/setup.py --setup
```

## setup script options

```sh
python scripts/setup.py --help

  --setup      symlink dotfiles to ~/.config
  --ssh        generate ssh key and configure
  --installs   install packages from setup.json
  --fonts      install nerd fonts
  --complete   do everything
```

## adding packages/fonts

edit `scripts/setup.json`, then re-run:

```sh
python scripts/setup.py --installs
python scripts/setup.py --fonts
```

## requirements

- macos (uses homebrew)
- python 3.12+
- zsh
