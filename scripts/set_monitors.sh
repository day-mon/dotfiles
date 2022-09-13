for m in $(xrandr --query | grep " connected" | cut -d" " -f1); do
    xrandr --output "$m" --rate 164.83 --mode 2560x1440     
    echo "Monitor $m set to 164.83 hz"
done
