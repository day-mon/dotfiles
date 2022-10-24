#!/usr/bin/env bash

# Add this script to your wm startup file.

DIR="$HOME/.config/polybar/shapes"

# Terminate already running bar instances
killall -q polybar

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

OTHERS=$(xrandr --query | grep " connected" | cut -d" " -f1)

# Launch on all other monitors
for m in $OTHERS; do
 MONITOR=$m polybar --reload -c $DIR/config.ini &
done
