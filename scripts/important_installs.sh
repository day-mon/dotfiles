#!/bin/sh

# Define escape codes for colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'
GREEN_UNDERLINE='\033[4;32m'

# Define functions for printing in different colors
print_yellow() {
    printf "${YELLOW}$1${NC}\n"
}
print_green() {
    printf "${GREEN}$1${NC}\n"
}
print_red() {
    printf "${RED}$1${NC}\n"
}

# Set list of packages to install
set -- paru topgrade bat exa go xsel feh picom flameshot docker xorg-xfd docker-compose zsh nemo neofetch kitty neovim discord betterdiscordctl jetbrains-toolbox nvim-packer-git enquirer youtubemusic

# Check if system is Arch Linux
if [ ! -f /etc/arch-release ]; then
    echo "🚫 Not on Arch Linux, exiting"
    exit 1
fi
printf "🔍 Arch Linux Check... ${GREEN}✅${NC}\n"

# Check for updates and perform update if necessary
UPDATES=$(checkupdates | wc -l)
if [ "$UPDATES" -ne 0 ]; then
    printf "🔄 Attempting to update ${GREEN_UNDERLINE}${UPDATES}${NC} packages\n"
    if sudo pacman -Syyu --noconfirm --quiet; then
      printf "🔄 Update check (${GREEN_UNDERLINE}${UPDATES}${NC} packages)... ${GREEN}✅${NC}\n"
    else
      printf "🔄 Update check (Not successful).. ${RED}❌${NC}\n";
    fi
else
     printf "🔄 Update check (Nothing to update).. ${GREEN}✅${NC}\n"
fi

# Install packages
for i in "$@"; do
    if ! pacman -Qs "$i" > /dev/null 2>&1; then
        printf "📦 Installing ${GREEN_UNDERLINE}%s${NC}\n" "$i"
        if ! sudo pacman -S "$i" --noconfirm --quiet; then
           if ! paru -S "$i" --noconfirm --quiet; then
               print_red "🚫 Failed to install $i"
           fi
        else
            print_green "📦 Installed ${GREEN_UNDERLINE}$i${NC}"
        fi
    else
        print_yellow "📦 $i is already installed @ $(command -v "$i")"
    fi
done

# Set background image
if pacman -Qs "feh" > /dev/null 2>&1; then
   if feh --bg-fill ~/.important/dotfiles/wallpapers/wallpaper.jpg; then
       print_green "🖼 Background as been set via feh.... ${GREEN_UNDERLINE}✅${NC}"
    else 
        print_red "🖼 Setting background.... ${RED}❌${NC} (feh command failed)"
    fi
else 
    print_red "🖼 Setting background.... ${RED}❌${NC} (feh command not found)"
fi

print_green "🏁 Finished installing important things. Installing fonts 📜"
bash "$HOME/.important/dotfiles/scripts/install_fonts.sh"

