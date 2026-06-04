# /// script
# requires-python = ">=3.12"
# dependencies = [
#   'httpx',
#   'trio',
#   'cyclopts',
# ]
# ///

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import trio
from cyclopts import App
from rich.console import Console

app = App(
    backend="trio",
    help="Dotfiles setup — run specific steps or --complete for everything.",
    help_on_error=False,
)
console = Console()
error_console = Console(stderr=True)

CONFIG_PATH = trio.Path(__file__).parent / trio.Path("setup.json")


@dataclass(frozen=True)
class Paths:
    home: trio.Path
    ssh: trio.Path
    dotfiles: trio.Path
    home_config: trio.Path
    zshrc: trio.Path
    zshenv: trio.Path


async def get_paths() -> Paths:
    home = await trio.Path("~").expanduser()
    return Paths(
        home=home,
        ssh=home / ".ssh",
        dotfiles=home / ".important" / "dotfiles",
        home_config=home / ".config",
        zshrc=home / ".zshrc",
        zshenv=home / ".zshenv",
    )


async def run(cmd: list[str], *, check: bool = True):
    return await trio.run_process(cmd, check=check)


async def symlink(src: trio.Path, dst: trio.Path) -> None:
    if await dst.exists():
        if await dst.is_symlink():
            console.print(f"⚠️ {dst} -> {src} already exists", style="yellow")
            return
        error_console.print(f"{dst} exists and is not a symlink")
        return

    await dst.symlink_to(
        target=src,
        target_is_directory=await src.is_dir(),
    )
    console.print(f"✅ {dst} → {src}", style="green")



async def setup_ssh(paths: Paths):
    """Generate SSH key and configure ~/.ssh/config."""
    if not await paths.ssh.exists():
        await paths.ssh.mkdir(parents=True, exist_ok=True)
        await run(["chmod", "700", str(paths.ssh)])

    key_path = paths.ssh / "id_ed25519"

    if not await key_path.exists():
        await run(
            [
                "ssh-keygen",
                "-t",
                "ed25519",
                "-f",
                str(key_path),
                "-N",
                "",
                "-C",
                "dotfiles-setup",
            ]
        )

    ssh_config_path = paths.ssh / "config"
    config_block = f"""Host *
    UseKeychain yes
    AddKeysToAgent yes
    IdentityFile {key_path}
"""

    if not await ssh_config_path.exists():
        async with await trio.open_file(ssh_config_path, "w") as f:
            await f.write(config_block)
        await run(["chmod", "600", str(ssh_config_path)])

    await run(["ssh-add", str(key_path)], check=False)

    async with await trio.open_file(f"{key_path}.pub", "r") as f:
        console.print(await f.read())


async def dotfiles_setup(paths: Paths):
    """Symlink dotfiles and set up zsh configuration."""
    origin = await trio.run_process(
        ["git", "remote", "get-url", "origin"],
        capture_stdout=True,
        capture_stderr=True,
        check=False,
    )

    if origin.returncode != 0:
        return

    remote_url = origin.stdout.decode().strip()
    if urlparse(remote_url).scheme != "git":
        ssh_url = remote_url.replace("https://", "git@", 1).replace(".com/", ".com:", 1)
        await run(["git", "remote", "set-url", "origin", ssh_url])

    zsh_dir = paths.dotfiles / ".config" / "zsh"
    zsh_env = zsh_dir / ".zshenv"

    if not await zsh_dir.exists():
        await zsh_dir.mkdir(parents=True, exist_ok=True)

    if not await zsh_env.exists():
        async with await trio.open_file(zsh_env, "w") as f:
            await f.write("export ZDOTDIR=$HOME/.config/zsh\n")

    if not await paths.home_config.exists():
        await paths.home_config.mkdir(parents=True, exist_ok=True)

    await copy_claude_files(paths)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(symlink, zsh_dir / ".zshrc", paths.zshrc)
        nursery.start_soon(symlink, zsh_dir / ".zshenv", paths.zshenv)

        config_root = paths.dotfiles / ".config"
        if await config_root.exists():
            for entry in await config_root.iterdir():
                nursery.start_soon(
                    symlink,
                    entry,
                    paths.home_config / entry.name,
                )


# Entries under .claude/ that are symlinked instead of copied, so they stay
# version-controlled and live-editable from the dotfiles checkout.
CLAUDE_SYMLINK_DIRS = frozenset({"skills"})


async def copy_claude_files(paths: Paths) -> None:
    """Copy .claude/ contents from dotfiles to ~/.claude/.

    Entries named in ``CLAUDE_SYMLINK_DIRS`` are symlinked rather than copied.
    """
    src_claude = paths.dotfiles / ".claude"
    dst_claude = paths.home / ".claude"

    if not await src_claude.exists():
        return

    if not await dst_claude.exists():
        await dst_claude.mkdir(parents=True, exist_ok=True)

    for entry in await src_claude.iterdir():
        dst_entry = dst_claude / entry.name

        if entry.name in CLAUDE_SYMLINK_DIRS:
            if await dst_entry.is_symlink():
                await dst_entry.unlink()
            elif await dst_entry.exists():
                await trio.to_thread.run_sync(shutil.rmtree, dst_entry)
            await dst_entry.symlink_to(target=entry, target_is_directory=True)
            console.print(f"🔗 linked {entry.name}/ → ~/.claude/", style="green")
            continue

        if await entry.is_dir():
            if await dst_entry.exists():
                await trio.to_thread.run_sync(shutil.rmtree, dst_entry)
            await trio.to_thread.run_sync(shutil.copytree, entry, dst_entry)
            console.print(f"📁 copied {entry.name}/ → ~/.claude/", style="green")
        elif await entry.is_file():
            await trio.to_thread.run_sync(shutil.copy2, entry, dst_entry)
            console.print(f"📄 copied {entry.name} → ~/.claude/", style="green")


async def brew_bundle(paths: Paths):
    """Run `brew bundle` with the project Brewfile."""
    if not await trio.to_thread.run_sync(shutil.which, "brew"):
        return
    brewfile = paths.dotfiles / "Brewfile"
    if not await brewfile.exists():
        error_console.print("⚠️ Brewfile not found")
        return
    await run(["brew", "bundle", "--file", str(brewfile)])


async def uninstall_packages(packages: list[str]):
    """Uninstall the given brew packages."""
    if packages:
        await run(["brew", "uninstall"] + packages, check=False)


async def custom_installs(installs: dict[str, str]):
    """Run custom install scripts for each tool."""
    for name, cmd in installs.items():
        if await trio.to_thread.run_sync(shutil.which, name):
            console.print(f"⚠️ {name} already installed", style="yellow")
            continue
        console.print(f"🔧 installing {name}...")
        await run(["sh", "-c", cmd], check=False)


@app.default
async def main(
    *,
    setup: bool = False,
    ssh: bool = False,
    uninstalls: bool = False,
    installs: bool = False,
    complete: bool = False,
):
    """Dotfiles setup — run one or more steps.

    Pass no flags to see this help. Use --complete to run everything.
    """
    if not any([setup, ssh, uninstalls, installs, complete]):
        app.help_print()
        return

    paths = await get_paths()

    async with await trio.open_file(CONFIG_PATH, "r") as f:
        config = json.loads(await f.read())

    if ssh or complete:
        await setup_ssh(paths)

    if setup or complete:
        await dotfiles_setup(paths)

    if uninstalls or complete:
        await uninstall_packages(config.get("uninstall_packages", []))

    if installs or complete:
        await brew_bundle(paths)

    if installs or complete:
        await custom_installs(config.get("custom_installs", {}))


if __name__ == "__main__":
    app()
