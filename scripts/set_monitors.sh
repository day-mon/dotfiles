#!/bin/sh
REFRESH_RATE="$1"
if [[ -z "$REFRESH_RATE" ]]; 
then
	REFRESH_RATE="164.83"
	echo "Input was blank setting refresh rate to $REFRESH_RATE by default"
fi

if ! [[ "$REFRESH_RATE" =~ ^[+-]?[0-9]+\.?[0-9]*$ ]]; 
then 
    echo "Inputs must be a numbers | Input $REFRESH_RATE" 
    exit 0 
fi

for m in $(xrandr --query | grep " connected" | cut -d" " -f1); do
    xrandr --output "$m" --rate "$REFRESH_RATE" --mode 2560x1440     
    echo "Monitor $m set to $REFRESH_RATE hz"
done
