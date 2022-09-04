import subprocess
import platform
import os


home = os.path.expanduser("~")
abs_path = os.path.abspath(os.getcwd())


def print_success(message: str):
    print(f"✓ {message}")


def transform_path(path: str) -> str:
    return path.replace("~", home)


def path_exist(path: str) -> bool:
    return os.path.exists(transform_path(path))


def remove_file(path: str) -> (bool, str):
    try:
        os.remove(transform_path(path))
        return (True, "")
    except Exception as e:
        return (False, str(e))


def perform_link(source: str, dest: str) -> (bool, str):
    try:
        os.link(source, dest)
        return (True, "")
    except Exception as e:
        return (False, str(e))


def perform_rename(new_name: str, old_name: str) -> (bool, str):
    try:
        os.rename(transform_path(old_name), transform_path(new_name))
        return (True, "")
    except Exception as e:
        return (False, str(e))


kernel = platform.system().lower()

if kernel not in ("darwin", "linux"):
    raise Exception(f"You must have a unix based system to run this script. Your system {kernel}")

in_root_dir = path_exist(".git")
if not in_root_dir:
    raise Exception("Please start this script from the root directory")


zshrc_path = '~/.zshrc'
zshrc_exist = path_exist(zshrc_path)

if zshrc_exist:
    renamed, err = perform_rename(zshrc_path, f"{zshrc_path}.presetup")
    if not renamed:
        raise Exception(f"Error has occurred while trying to rename .zshrc file | Error {err}")

print_success("Successfully renamed .zshrc")

zsh_link_path = f"{abs_path}/zsh/.zshrc"
zsh_link, err = perform_link(zsh_link_path, "~/.zshrc")
if not zsh_link:
    raise Exception(f"Error has occurred while trying to link .zshrc file | Error {err}")

print_success(f"Successfully linked .zshrc with {zsh_link_path}")

nvim_config_path = "~/.config/nvim"

nvim_config_exist = path_exist(nvim_config_path)
if not nvim_config_exist:
    # using sub process to see the result here
    directory_result = subprocess.run(args=["mkdir", nvim_config_path])
    if directory_result.returncode != 0:
        raise Exception("Error occurred while trying to make directory for Neo-Vim")

# check if link exist first
init_lua_path = f"{nvim_config_path}/init.lua"
init_lua_linked = os.path.islink(init_lua_path)

if init_lua_linked:
    print_success("init.lua has already been linked. Nice :)")

if not init_lua_linked:
    # check if init.lua or init.vim exist first
    init_vim_path = f"{nvim_config_path}/init.vim"
    init_lua_exist = path_exist(init_lua_path)
    init_vim_exist = path_exist(init_vim_path)

    if init_lua_exist:
        init_lua_removed, err = remove_file(init_lua_path)
        if not init_lua_removed:
            raise Exception(f"An error has occurred while trying to remove init.lua | Error ${err}")

    if init_vim_exist:
        init_vim_removed, err = remove_file(init_vim_path)
        if not init_vim_exist:
            raise Exception(f"An error has occurred while trying to remove init.vim | Error {err}")

    init_lua_link_path = f"{abs_path}/nvim/init.lua"
    link_attempt_success, err = perform_link(init_lua_link_path, f"{home}/.config/nvim/init.lua")

    if not link_attempt_success:
        raise Exception(f"An error has occurred while trying to perform the link of init.lua | Error: {err}")

    print_success(f"Successfully linked init.lua to {init_lua_link_path}")
