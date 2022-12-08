#!/bin/sh

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'
GREEN_UNDERLINE='\033[4;32m'

print_yellow() {
    printf "${YELLOW}$1${NC}\n"
}
print_green() {
    printf "${GREEN}$1${NC}\n"
}
print_red() {
    printf "${RED}$1${NC}\n"
}


# POSIX Array
set -- paru topgrade bat exa go xsel feh flameshot docker xorg-xfd docker-compose zsh nemo neofetch kitty neovim discord betterdiscordctl jetbrains-toolbox nvim-packer-git youtubemusic

# Check to see if we are on arch linux
if [ ! -f /etc/arch-release ]; then
    echo "Not on arch linux, exiting"
    exit 1
fi
printf "Arch Linux Check... ${GREEN}OK${NC}\n"

UPDATES=$(checkupdates | wc -l)

if "$UPDATES" -ne 0; then
    printf "Attempting to update ${GREEN_UNDERLINE}${UPDATES}${NC} packages\n"
    if sudo pacman -Syyu --noconfirm --quiet; then
      printf "Update check (${GREEN_UNDERLINE}${UPDATES}${NC} packages)... ${GREEN}OK${NC}\n"
    else
      printf "Update check (Not successful).. ${RED}FAILED${NC}\n";
    fi
else
     printf "Update check (Nothing to update).. ${GREEN}OK${NC}\n"
fi

for i in "$@"; do
    if ! pacman -Qs "$i" > /dev/null 2>&1; then
        printf "Installing ${GREEN_UNDERLINE}%s${NC}\n" "$i"
        if ! sudo pacman -S "$i" --noconfirm --quiet; then
           if ! yay -S "$i" --noconfirm --quiet; then
               print_red "Failed to install $i"
           fi
        else
            print_green "Installed ${GREEN_UNDERLINE}$i${NC}"
        fi
    else
        print_yellow "$i is already installed @ $(command -v "$i")"
    fi
done


if pacman -Qs "feh" > /dev/null 2>&1; then
   if feh --bg-fill ~/.important/dotfiles/wallpapers/wallpaper.jpg; then
       printf "Setting background.... ${GREEN_UNDERLINE}OK${NC}\n"
    else 
        printf "Setting background.... ${RED}FAILED${NC} (feh command failed)\n"
    fi
else 
    print_red "Setting background.... ${RED}FAILED${NC} (feh command not found)\n"
fi

echo "Finished installing important things. Installing fonts :)"
bash "$HOME/.important/dotfiles/scripts/install_fonts.sh"
