import shutil
import subprocess
from typing import Optional


def is_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except ValueError:
        return None


def main():
    if shutil.which("xrandr") is None:
        print("xrandr not found")
        return

    # Get the list of monitors
    monitors = subprocess.check_output(["xrandr", "--query"]).decode("utf-8")

    # get the connected monitors and the line below
    monitors = monitors.split("\n")
    monitors = [(monitor.split()[0], monitors[index + 1]) for index, monitor in enumerate(monitors) if " connected" in monitor]

    # get all odd indexes
    monitors = monitors[::1]

    for monitor in monitors:
        output, refresh_rate = monitor
        rates = refresh_rate.split()
        resolution = rates.pop(0)

        all_rates = [float(n.replace('*', '')) for n in rates if is_float(n.replace('*', ''))]
        max_refresh = max(all_rates)

        command_to_run = ['xrandr', '--output', f'{output}', '--mode', f'{resolution}', '--rate', f'{max_refresh}']
        print(f'Getting ready to run {command_to_run}')
        subprocess.call(command_to_run)


if __name__ == "__main__":
    main()
