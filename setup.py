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
        return True, ""
    except Exception as e:
        return False, str(e)


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
        os.link(transform_path(source), transform_path(dest))
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
    if not folder_exist:
        folder_removed, folder_removed_message = remove_file(folder_path)
        if not folder_removed:
            raise Exception(folder_removed_message)

    link_path = f"{abs_path}/{name}"
    link_path_success, link_message = perform_link(folder_path, link_path)
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

if zshrc_exist:
    renamed, err = perform_rename(zshrc_path, f"{zshrc_path}.presetup")
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

# nvim_config_path = "~/.config/nvim"
#
# nvim_config_exist = path_exist(nvim_config_path)
# if not nvim_config_exist:
#     # using sub process to see the result here
#     directory_result = subprocess.run(args=["mkdir", nvim_config_path])
#     if directory_result.returncode != 0:
#         raise Exception("Error occurred while trying to make directory for Neo-Vim")
#
# # check if init.lua or init.vim exist first
# init_lua_path = f"{nvim_config_path}/init.lua"
# init_vim_path = f"{nvim_config_path}/init.vim"
#
# init_lua_exist = path_exist(init_lua_path)
# init_vim_exist = path_exist(init_vim_path)
#
# if init_lua_exist:
#     init_lua_removed, lua_err = remove_file(init_lua_path)
#     if not init_lua_removed:
#         raise Exception(f"An error has occurred while trying to remove init.lua | Error {lua_err}")
#
# if init_vim_exist:
#     init_vim_removed, vim_er = remove_file(init_vim_path)
#     if not init_vim_exist:
#         raise Exception(f"An error has occurred while trying to remove init.vim | Error {vim_er}")
#
# init_lua_link_path = f"{abs_path}/nvim/init.lua"
# link_attempt_success, link_message = perform_link(init_lua_link_path, f"{home}/.config/nvim/init.lua")
#
# if not link_attempt_success:
#     raise Exception(f"An error has occurred while trying to perform the link of init.lua | Error: {link_message}")
#
# print_success(link_message)
#
# # check if lua folder exist
# lua_folder_path = f"{nvim_config_path}/lua"
# lua_folder_exist = path_exist(lua_folder_path)
#
# if lua_folder_exist:
#     lua_folder_removed, lua_folder_err = remove_file(lua_folder_path)
#     if not lua_folder_removed:
#         raise Exception(f"An error has occurred while trying to remove lua folder | Error {lua_folder_err}")
#
# lua_folder_link_path = f"{abs_path}/nvim/lua"
# lua_folder_link_success, lua_folder_link_message = perform_link(lua_folder_link_path, lua_folder_path)
# if not lua_folder_link_success:
#     raise Exception(f"An error has occurred while trying to link lua folder | Error {lua_folder_link_message}")
#
# print_success(lua_folder_link_message)
#
# # check if polybar folder exist
# polybar_folder_path = f"{home}/.config/polybar"
# polybar_folder_exist = path_exist(polybar_folder_path)
#
# if polybar_folder_exist:
#     polybar_folder_removed, polybar_folder_err = remove_file(polybar_folder_path)
#     if not polybar_folder_removed:
#         raise Exception(f"An error has occurred while trying to remove polybar folder | Error {polybar_folder_err}")
#
# polybar_folder_link_path = f"{abs_path}/polybar"
# polybar_folder_link_success, polybar_folder_link_message = perform_link(polybar_folder_link_path, polybar_folder_path)
# if not polybar_folder_link_success:
#     raise Exception(f"An error has occurred while trying to link polybar folder | Error {polybar_folder_link_message}")
#
# print_success(polybar_folder_link_message)
#
# # check if rofi folder exist
# rofi_folder_path = f"{home}/.config/rofi"
# rofi_folder_exist = path_exist(rofi_folder_path)
#
# if rofi_folder_exist:
#     rofi_folder_removed, rofi_folder_err = remove_file(rofi_folder_path)
#     if not rofi_folder_removed:
#         raise Exception(f"An error has occurred while trying to remove rofi folder | Error {rofi_folder_err}")
#
# rofi_folder_link_path = f"{abs_path}/rofi"
# rofi_folder_link_success, rofi_folder_link_message = perform_link(rofi_folder_link_path, rofi_folder_path)
# if not rofi_folder_link_success:
#     raise Exception(f"An error has occurred while trying to link rofi folder | Error {rofi_folder_link_message}")
#
# print_success(rofi_folder_link_message)
#
# # check if kitty folder exist
# kitty_folder_path = f"{home}/.config/kitty"
# kitty_folder_exist = path_exist(kitty_folder_path)
#
# if kitty_folder_exist:
#     kitty_folder_removed, kitty_folder_err = remove_file(kitty_folder_path)
#     if not kitty_folder_removed:
#         raise Exception(f"An error has occurred while trying to remove kitty folder | Error {kitty_folder_err}")
#
# kitty_folder_link_path = f"{abs_path}/kitty"
# kitty_folder_link_success, kitty_folder_link_message = perform_link(kitty_folder_link_path, kitty_folder_path)
# if not kitty_folder_link_success:
#     raise Exception(f"An error has occurred while trying to link kitty folder | Error {kitty_folder_link_message}")
#
# print_success(kitty_folder_link_message)
