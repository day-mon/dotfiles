#!/usr/bin/env bash

FONTS=(
  "https://github.com/ryanoasis/nerd-fonts/releases/download/v2.2.2/JetBrainsMono.zip"
  "https://github.com/ryanoasis/nerd-fonts/releases/download/v2.2.2/3270.zip"
  "https://github.com/ryanoasis/nerd-fonts/releases/download/v2.2.2/FiraCode.zip"
)


if [ ! -d "$HOME/.local/share/fonts" ]; then
  mkdir -p "$HOME/.local/share/fonts"
fi

for font in "${FONTS[@]}"; do
  wget -O "$HOME/.local/share/fonts/$(basename "$font")" "$font"
  unzip -o "$HOME/.local/share/fonts/$(basename "$font")" -d "$HOME/.local/share/fonts"
done

fc-cache -f -v
rm -rf *.zip *.txt *.md
