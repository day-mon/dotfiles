import os
import subprocess
from typing import List
from urllib.parse import urlparse
import shutil
import argparse
from sys import platform
import requests
import json
import zipfile
from pathlib import Path

RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
NC = '\033[0m'


def print_yellow(text):
    print(f"{YELLOW}{text}{NC}")


def print_green(text):
    print(f"{GREEN}{text}{NC}")


def print_red(text):
    print(f"{RED}{text}{NC}")


def symlink(src, dst):
    # check if sym link exists
    if os.path.islink(dst):
        print_yellow(f"🔗 {dst} is already symlinked to {os.readlink(dst)}")
        return

    try:
        os.symlink(src, dst)
        print_green(f"🔗 Symlinked {src} to {dst}\n")
    except:
        print_red(f"🚫 Symlink failed {src} to {dst}\n")


def setup():
    remote_url = subprocess.check_output(["git", "remote", "get-url", "origin"]).decode().strip()

    # check if its an ssh url or not
    parsed = urlparse(remote_url)
    if parsed.scheme != 'git':
        remote_url = remote_url.replace("https://", "git@", 1).replace(".com/", ".com:", 1)
        subprocess.run(["git", "remote", "set-url", "origin", remote_url])
        print_green("🔐 SSH URL Check (Switching to SSH)... ✅\n")
    else:
        print_yellow("🔐 SSH URL Check (Already set)... ✅\n")

    ssh_dir = os.path.expanduser("~/.ssh")
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir)

    dotfiles_dir = os.path.join(os.path.expanduser("~/.important/dotfiles"))
    zsh_directory = f"{dotfiles_dir}/.config/zsh"

    if not os.path.exists(f"{zsh_directory}/.zshenv"):
        with open(f"{zsh_directory}/.zshenv", "x") as file:
            file.write("export ZDOTDIR=$HOME/.config/zsh\n")
        print("📝 Created .zshenv file, place your env variables here")

    print("🔗 Establishing Sym Links...")
    symlink(os.path.join(zsh_directory, ".zshrc"), os.path.join(os.path.expanduser("~/.zshrc")))
    symlink(os.path.join(zsh_directory, ".zshenv"), os.path.join(os.path.expanduser("~/.zshenv")))

    config_dir = os.path.join(dotfiles_dir, ".config")
    for file in os.listdir(config_dir):
        symlink(os.path.join(config_dir, file), os.path.join(os.path.expanduser("~/.config"), file))


def important_installs(packages: List[str]):
    if not shutil.which("pacman") and not shutil.which("brew"):
        print_red("🚫 Pacman or Brew not found... ❌")
        exit(1)

    print_green(f"🔍 You are running {platform.lower()}  ✅")

    if not shutil.which("git"):
        print("📦 Git not found.. Installing so we can continue")
        if not shutil.which('pacman'):
            subprocess.run(["brew", "install", "git"])
        else:
            subprocess.run(["sudo", "pacman", "--noconfirm", "-S", "git"])

    if not shutil.which("paru") and shutil.which('pacman'):
        subprocess.run(["sudo", "pacman", "-S", "--needed", "base-devel"])
        subprocess.run(["git", "clone", "https://aur.archlinux.org/paru.git"])
        subprocess.run(["makepkg", "-si"], cwd="paru")
        shutil.rmtree("paru")

    if shutil.which('pacman'):
        subprocess.run(["sudo", "pacman", "-Syyu", "--noconfirm", "--quiet"])
    else:
        subprocess.run(["brew", "update"])

    already_installed = 0
    installed = 0
    failed_installs = 0

    for package in packages:
        args_to_run = ["sudo", "pacman", "-S", "--noconfirm", "--quiet", package] if shutil.which('pacman') else [
            "brew", "install", package
        ]

        sp = subprocess.run(args_to_run, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
        if sp.returncode == 0:
            already_installed += 1
            print_yellow(f"🔍 {package} is already installed")
            continue

        args_to_run = ["paru", "-S", "--noconfirm", "--quiet", package] if shutil.which('pacman') else [
            "brew", "install", package
        ]

        sp = subprocess.run(args_to_run, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
        if sp.returncode == 0:
            installed += 1
            print_green(f"✅ Installed {package}")
            continue

        if shutil.which('pacman'):
            sp = subprocess.run(["paru", "-S", "--noconfirm", "--quiet", package], stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
            if sp.returncode == 0:
                installed += 1
                print_green(f"✅ Installed {package}")
                continue

        failed_installs += 1
        print_red(f"🚫 Failed to install {package}")

    print_green(f"\n✅ Installed {installed} packages")
    print(f""" Summary
    ✅ Already Installed: {already_installed}
    ✅ Installed: {installed}/{len(packages)}
    🚫 Failed Installs: {failed_installs}
    """)

    if shutil.which("feh"):
        wallpaper_location = os.path.expanduser("~/.important/dotfiles/wallpapers/wallpaper.jpg")

        bg = subprocess.run(["feh", "--bg-fill", f"{wallpaper_location}"])
        if bg.returncode != 0:
            print_red("🖼 Setting background....❌ (feh command failed)")


def install_fonts(fonts: List[str]):
    if shutil.which('brew'):
        tap = subprocess.run(['brew', 'tap', 'homebrew/cask-fonts'])
        if tap.returncode != 0:
            print_red("Could not tap homebrew/cask-fonts")
            exit(1)

        install = subprocess.run(['brew', 'install', '--cask', 'font-hack-nerd-font'])
        if install.returncode != 0:
            print_red("Could not install font-hack-nerd-font")
            exit(1)

        print_green("✅ Fonts installed successfully!")
        return

    # Create .local/share/fonts directory if it doesn't exist
    font_dir = Path.home() / ".local" / "share" / "fonts"
    font_dir.mkdir(parents=True, exist_ok=True)

    # Download and unzip fonts
    for font_url in fonts:
        font_name = os.path.basename(font_url)
        font_zip = font_dir / font_name

        # Download font zip file
        print(f"📥 Downloading {font_url}...")
        response = requests.get(font_url)
        if response.status_code != 200:
            print(f"❌ Could not download {font_name}, skipping...")
            continue
        with open(font_zip, "wb") as file:
            file.write(response.content)
        print(f"✅ Downloaded {font_name}")

        # Unzip font zip file
        print(f"📦 Unzipping {font_name}...")
        try:
            with zipfile.ZipFile(font_zip, "r") as zip_ref:
                zip_ref.extractall(font_dir)
        except zipfile.BadZipFile:
            print(f"❌ Could not unzip {font_name}, skipping...")
            continue
        print(f"✅ Unzipped & Installed {font_name}")

    # Update font cache
    print("🔄 Updating font cache...")
    try:
        os.system("fc-cache -f -v")
    except OSError:
        print("❌ Could not update font cache")
        exit(1)
    print("✅ Font cache updated!")

    # Cleanup downloaded zip files
    print("🗂️ Running cleanup...")
    for font_url in fonts:
        font_name = os.path.basename(font_url)
        font_zip = font_dir / font_name
        font_zip.unlink(missing_ok=True)
    print("✅ Cleaned up all zips")
    print("✅ Fonts installed successfully")


def uninstall():
    if platform.lower() != 'linux':
        print("ℹ️ Bailing not linux")
        return

    packages = ['i3status', 'i3blocks']

    for package in packages:
        spc = subprocess.run(['sudo', 'pacman', '-Q', package], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        if spc.returncode == 1:
            print_green(f"✅ {package} already doesnt exit")
            continue

        sp = subprocess.run(["sudo", "pacman", "-R", "--noconfirm", package], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
        if sp.returncode == 0:
            print_green(f"✅ Uninstalled {package}")
        else:
            print_red(f"🚫 Failed to uninstall {package}")


def is_desktop():
    """
    Checks if the current machine is a desktop or not, by checking if display is set
    """
    return os.environ.get('DISPLAY') is not None

def main():
    parser = argparse.ArgumentParser(description='Setup dotfiles')
    parser.add_argument('--setup', action='store_true', help='Setup dotfiles')
    parser.add_argument('--uninstalls', action='store_true', help='Uninstalls common packages that are annoying')
    parser.add_argument('--installs', action='store_true', help='Install important packages')
    parser.add_argument("--fonts", action='store_true', help='Install fonts')
    parser.add_argument("--files", action='store_true', help='Setup env files and the like')
    parser.add_argument("--all", action='store_true', help="Install all")
    args = parser.parse_args()

    if not os.path.exists("setup.json"):
        print_red("🚫 setup.json has not been found")
        exit(1)

    if not (args.setup or args.installs or args.uninstalls or args.fonts or args.all):
        print_red("🚫 No arguments passed... ❌")
        exit(1)

    setup_file = open('setup.json', mode='r')
    setup_json = json.load(setup_file)

    packages = setup_json.get('packages_server', [])
    if is_desktop():
        print_yellow("🖥️ Running on a desktop, adding desktop packages")
        packages.extend(setup_json.get('packages_desktop', []))

        

    fonts = setup_json.get('fonts', [])

    if args.setup or args.all:
        setup()

    if args.uninstalls or args.all:
        uninstall()

    if args.installs or args.all:
        important_installs(packages)

    if args.fonts or args.all:
        install_fonts(fonts)

    print_green("🎉 Setup Complete 🎉")


if __name__ == "__main__":
    main()
