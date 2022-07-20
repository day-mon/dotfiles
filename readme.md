common problems: 
zoom being weird:
 - https://www.reddit.com/r/archlinux/comments/nqiudn/problems_with_launching_zoom/

requirements:
for vim:
- vim-plugged (https://github.com/junegunn/vim-plug)
   - sh -c 'curl -fLo "${XDG_DATA_HOME:-$HOME/.local/share}"/nvim/site/autoload/plug.vim --create-dirs \
       https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'

for zsh:
 - antigen (https://github.com/zsh-users/antigen)
   - curl -L git.io/antigen > /.hidden/antigen.zsh
