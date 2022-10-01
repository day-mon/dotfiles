#!/bin/sh
MONITOR_SIZE=""
RATE=""
OUTPUT=""
I=1
for m in $(xrandr --query | grep -A1 " connected" | awk '{print $1; print $4}' | sed "s/*//g;" | sed "s/(normal//g;" | sed "s/--//g" | sed '/^[[:space:]]*$/d'); do

    if [ $I -eq  1 ]; then
    	OUTPUT=$m
    fi

    if [ $I -eq 2 ]; then
    	MONITOR_SIZE=$m
    fi

    if [ $I -eq 3 ]; then
	    RATE=$m
	    xrandr --output "$OUTPUT" --mode "$MONITOR_SIZE" --rate "$RATE"
	    echo "Setting $OUTPUT to $MONITOR_SIZE at $RATE"
	    I=0
	    MONITOR_SIZE=""
	    RATE=""
	    OUTPUT=""
    fi

   I=$((I=I+1))
done
