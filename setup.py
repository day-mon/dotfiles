import datetime
import subprocess
import platform
import os
from pathlib import Path

home = os.path.expanduser("~")
abs_path = os.path.abspath(os.getcwd())


def print_success(message: str):
    print(f"✓ {message}")


def transform_path(path: str) -> str:
    return path.replace("~", home)


def is_sym_link(path: str):
    subprocess


def path_exist(path: str) -> bool:
    return os.path.exists(transform_path(path))


def remove_path(path: str) -> (bool, str):
    remove_process = subprocess.run(args=["rm", "-rf", transform_path(path)])
    if remove_process.returncode != 0:
        return False, f"Error removing {path} with code {remove_process.returncode} and output {remove_process.stderr}"
    return True, ""


def perform_link(source: str, dest: str) -> (bool, str):
    source = transform_path(source)
    dest = transform_path(dest)

    if os.path.islink(dest):
        if os.readlink(dest) == source:
            return True, f"Link to {dest} already established to {source}"

        try:
            os.unlink(dest)
        except Exception as e:
            return False, str(e)

    try:
        os.symlink(source, dest)
        return True, f"Link successfully established {source} -> {dest}"
    except Exception as e:
        return False, str(e)


def perform_rename(new_name: str, old_name: str) -> (bool, str):
    try:
        os.rename(transform_path(new_name), transform_path(old_name))
        return True, ""
    except Exception as e:
        return False, str(e)


def perform_full_link(name: str):
    folder_path = f"{home}/.config/{name}"
    folder_exist = path_exist(folder_path)

    if folder_exist and not os.path.islink(folder_path):
        folder_removed, folder_removed_message = remove_path(folder_path)
        if not folder_removed:
            raise Exception(folder_removed_message)

    link_path = f"{abs_path}/{name}"
    link_path_success, link_message = perform_link(link_path, folder_path)
    if not link_path_success:
        raise Exception(link_message)

    print_success(link_message)


kernel = platform.system().lower()

if kernel not in ("darwin", "linux"):
    raise Exception(f"You must have a unix based system to run this script. Your system {kernel}")

in_root_dir = path_exist(".git")
if not in_root_dir:
    raise Exception("Please start this script from the root directory")

zshrc_path = '~/.zshrc'
zshrc_exist = path_exist(zshrc_path)

if zshrc_exist and not os.path.islink(transform_path(zshrc_path)):
    renamed, err = perform_rename(zshrc_path, f"{zshrc_path}.presetup-{int(datetime.datetime.now().timestamp())}")
    if not renamed:
        raise Exception(f"Error has occurred while trying to rename .zshrc file | Error {err}")
    print_success("Successfully renamed .zshrc")

zsh_link_path = f"{abs_path}/zsh/.zshrc"
zshrc_path = transform_path("~/.zshrc")
zsh_link, zsh_link_message = perform_link(zsh_link_path, zshrc_path)

if not zsh_link:
    raise Exception(f"Error has occurred while trying to link .zshrc file | Error: {zsh_link_message}")

print_success(zsh_link_message)

names = ['nvim', 'polybar', 'rofi', 'kitty']
for name in names:
    perform_full_link(name)

print_success("Setup complete!")
