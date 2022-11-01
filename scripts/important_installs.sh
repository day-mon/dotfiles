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
set -- paru rustc bat go xsel flameshot docker docker-compose zsh nemo neofetch kitty

# Check to see if we are on arch linux
if [ ! -f /etc/arch-release ]; then
    echo "Not on arch linux, exiting"
    exit 1
fi
printf "Arch Linux Check... ${GREEN}OK${NC}\n"

UPDATES=$(checkupdates | wc -l)

if [ ! "$UPDATES" -eq 0 ]; then
    printf "Attempting to update ${GREEN_UNDERLINE}${UPDATES}${NC} packages\n"
    if [ $(sudo pacman -Syyu --noconfirm --quiet) ]; then
      printf "Update check (${GREEN_UNDERLINE}${UPDATES}${NC} packages)... ${GREEN}OK${NC}"
    else
      printf "Update check (Not successful).. ${RED}FAILED${NC}";
    fi
else
    printf "Update check (Nothing to update).. ${GREEN}OK${NC}\n"
fi

for i in "$@"; do
    if ! command -v "$i" > /dev/null 2>&1; then

        printf "Installing ${GREEN_UNDERLINE}%s${NC}\n" "$i"
        if [ ! $(sudo pacman -S "$i" --noconfirm --quiet) -eq 0 ]; then
           [ ! $(paru -S "$i" --noconfirm --quiet) -eq 0 ] print_red "Failed to install $i"
        else
            print_green "Installed ${GREEN_UNDERLINE}$i${NC}"
        fi
    else
        print_yellow "$i is already installed @ $(command -v "$i")"
    fi
done
