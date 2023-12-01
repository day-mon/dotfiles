## To get started
```sh
git clone https://github.com/day-mon/dotfiles.git ~/.important/dotfiles &&
cd ~/.important/dotfiles/scripts && 
sh setup.sh &&
nivim --headless +PackerInstall +q
```

## Some common problems I run into
zoom being weird:
- https://www.reddit.com/r/archlinux/comments/nqiudn/problems_with_launching_zoom/

starship themes not showing up:
- https://github.com/starship/starship/discussions/1600

packer not working:
- https://github.com/wbthomason/packer.nvim/issues/943

- ran into an issue where letters would double type themselves, fixed by removing xterm-kitty because set to TERM env variable
