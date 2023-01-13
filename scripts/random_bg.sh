#!/bin/bash

if ! hash feh; then
    echo "Feh not installed"
    exit
fi

# Set the directory containing the background images
bg_dir="$HOME/.important/dotfiles/wallpapers"

# Get a random background image from the directory
bg_image=$(find "$bg_dir" -type f | shuf -n 1)

# Set the background image
feh --bg-fill "$bg_image"

