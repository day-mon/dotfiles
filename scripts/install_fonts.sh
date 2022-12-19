#!/usr/bin/env bash

# Display a message in green
function green {
  printf "\033[32m$1\033[0m\n"
}

# Display a message in red
function red {
  printf "\033[31m$1\033[0m\n"
}


if [ "$(uname)" == "Darwin" ]; then
    brew tap homebrew/cask-fonts
    brew install --cask font-hack-nerd-font
    green "✅  Fonts installed successfully"
    exit
fi


# URLs to zip files with fonts
FONTS=(
  "https://github.com/ryanoasis/nerd-fonts/releases/download/v2.2.2/JetBrainsMono.zip"
  "https://github.com/ryanoasis/nerd-fonts/releases/download/v2.2.2/3270.zip"
  "https://github.com/ryanoasis/nerd-fonts/releases/download/v2.2.2/FiraCode.zip"
)


# Create .local/share/fonts directory if it doesn't exist
if [ ! -d "$HOME/.local/share/fonts" ]; then
  green "🗂️  Creating .local/share/fonts directory..."
  mkdir -p "$HOME/.local/share/fonts"
fi

# Download and unzip fonts
for font in "${FONTS[@]}"; do
  font_name=$(basename "$font")
  font_zip="$HOME/.local/share/fonts/$font_name"

  # Download font zip file
  echo "📥  Downloading $font..."
  if ! wget -q -O  "$font_zip" "$font"; then
      red "❌  Could not download $font_name, skipping..."
      continue
  fi
  green "✅  Dowloaded $font"


  # Unzip font zip file
  echo "📦  Unzipping $font..."
  if ! unzip -q -o "$font_zip" -d "$HOME/.local/share/fonts"; then
      red "❌  Could not unzip $font_name, skipping..."
      continue
  fi
  green "✅  Unzipped & Installed $font"
done

# Update font cache
echo "🔄  Updating font cache..."
if ! fc-cache -f -v > /dev/null; then
  red "❌  Could not update font cache"
  exit 1
fi
green "✅  Font cache updated!"



echo "🗂️  Running cleanup..."
# Delete downloaded zip files
for font in "${FONTS[@]}"; do
  font_name=$(basename "$font")
  font_zip="$HOME/.local/share/fonts/$font_name"
  rm "$font_zip"
done
green "✅  Cleaned up all zips"
green "✅  Fonts installed successfully"
