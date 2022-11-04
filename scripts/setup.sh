#!/usr/bin/env bash
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


symlink() {
  # check if sym link exists
  if [ $(readlink "$2") ]; then
    print_yellow "$2 is already symlinked to $(readlink "$2")"
    return
  fi

  if [ $(ln -s "$1" "$2") ]; then
    printf "Symlinked ${GREEN_UNDERLINE}$1${NC} to ${GREEN_UNDERLINE}$2${NC}\n"
  else
    printf "Symlinked failed ${RED_UNDERLINE}$1${NC} to ${RED_UNDERLINE}$2${NC}\n"
  fi
}

REMOTE_URL=$(git remote get-url origin)

# check if its an ssh url or not
if [ "${REMOTE_URL:0:4}" != "git@" ]; then
    REMOTE_URL=$(echo "$REMOTE_URL" | sed -e "s/https:\/\//git@/g" -e "s/\.com:/\.com:/g")
    git remote set-url origin "$REMOTE_URL"
    printf "SSH URL Check (Swich to SSH)... ${GREEN}OK${NC}\n"
else
  printf "SSH URL Check (Already set)... ${GREEN}OK${NC}\n"
fi


if [ ! -f "${HOME}/.ssh" ]; then
    mkdir -p "${HOME}/.ssh"
fi

# find directory of this script
DIR="$(cd"$(dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DOTFILES_DIR="$(realpath "$DIR")"

echo "${DOTFILES_DIR}"

#CONFIG_SYM=(kitty nvim zsh)

# Establish Sym Links
#symlink "${DOTFILES_DIR}/.zshrc" "${HOME}/.zshrc"

#for val in "${CONFIG_SYM[@]}"; do
#  symlink "${DOTFILES_DIR}/.config/${val}" "${HOME}/.config/${val}"
#done

#print_green "Finished setting up dotfiles.. Executing important_installs.sh"
#bash "${DOTFILES_DIR}/important_installs.sh"
