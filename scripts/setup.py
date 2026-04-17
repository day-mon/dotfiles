# /// script
# requires-python = ">=3.12"
# dependencies = [
#   'httpx',
#   'trio',
#   'asyncclick'
# ]
# ///

import json
import shutil
from dataclasses import dataclass
from urllib.parse import urlparse

import asyncclick as click
import trio


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
            click.secho(f"⚠️{dst} -> {src} already exists", fg="yellow")
            return
        click.echo(f"{dst} exists and is not a symlink", err=True)
        return

    await dst.symlink_to(
        target=src,
        target_is_directory=await src.is_dir(),
    )
    click.secho(f"✅ {dst} → {src}", fg="green")


async def setup_ssh(paths: Paths):
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
        click.echo(await f.read())


async def dotfiles_setup(paths: Paths):
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

    # copy .claude/ contents to ~/.claude/
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


async def copy_claude_files(paths: Paths) -> None:
    """Copy .claude/ contents from dotfiles to ~/.claude/"""
    src_claude = paths.dotfiles / ".claude"
    dst_claude = paths.home / ".claude"

    if not await src_claude.exists():
        return

    if not await dst_claude.exists():
        await dst_claude.mkdir(parents=True, exist_ok=True)

    for entry in await src_claude.iterdir():
        dst_entry = dst_claude / entry.name
        if await entry.is_dir():
            if await dst_entry.exists():
                shutil.rmtree(dst_entry)
            shutil.copytree(entry, dst_entry)
            click.secho(f"📁 copied {entry.name}/ → ~/.claude/", fg="green")
        elif await entry.is_file():
            shutil.copy2(entry, dst_entry)
            click.secho(f"📄 copied {entry.name} → ~/.claude/", fg="green")


async def brew_bundle(paths: Paths):
    if not shutil.which("brew"):
        return
    brewfile = paths.dotfiles / "Brewfile"
    if not await brewfile.exists():
        click.echo("⚠️ Brewfile not found", err=True)
        return
    await run(["brew", "bundle", "--file", str(brewfile)])


async def uninstall_packages(packages: list[str]):
    if packages:
        await run(["brew", "uninstall"] + packages, check=False)


async def custom_installs(installs: dict[str, str]):
    for name, cmd in installs.items():
        if shutil.which(name):
            click.secho(f"⚠️ {name} already installed", fg="yellow")
            continue
        click.echo(f"🔧 installing {name}...")
        await run(["sh", "-c", cmd], check=False)


async def install_uv_tools(tools: list[str], upgrade: bool = False):
    if not tools or not shutil.which("uv"):
        click.echo("⚠️ uv not found, skipping uv tool installs", err=True)
        return
    for tool in tools:
        click.echo(f"📦 uv tool install {tool}...")
        cmd = ["uv", "tool", "install"]
        if upgrade:
            cmd.append("--upgrade")
        cmd.append(tool)
        await run(cmd, check=False)


@click.command()
@click.option("--setup", is_flag=True)
@click.option("--ssh", is_flag=True)
@click.option("--uninstalls", is_flag=True)
@click.option("--installs", is_flag=True)
@click.option("--fonts", is_flag=True)
@click.option("--complete", is_flag=True)
@click.option("--upgrade", is_flag=True, help="upgrade existing uv tools")
@click.pass_context
async def main(
    ctx: click.Context,
    setup: bool,
    ssh: bool,
    uninstalls: bool,
    installs: bool,
    fonts: bool,
    complete: bool,
    upgrade: bool,
):
    if not any([setup, ssh, uninstalls, installs, fonts, complete]):
        click.echo(ctx.get_help())
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
        await install_uv_tools(config.get("uv_tools", []), upgrade=upgrade)


if __name__ == "__main__":

    main(_anyio_backend="trio")
