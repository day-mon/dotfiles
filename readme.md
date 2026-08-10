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

# run full setup (installs uv, then symlinks + packages + ssh key)
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

## adding packages

edit `Brewfile` for homebrew packages (macOS), `Aptfile` for apt packages (Linux), or
edit `scripts/setup.json` for uv tools and custom installs, then re-run:

```sh
uv run scripts/setup.py --installs
```

`--installs` runs the package manager present on the host: `brew bundle` on
macOS, `apt-get install` from the Aptfile on Debian/Ubuntu (via `sudo -n`),
plus any `custom_installs` from `setup.json`.

## requirements

- macos (uses homebrew) or linux (uses apt-get)
- [uv](https://docs.astral.sh/uv/)
- zsh
