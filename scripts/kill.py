#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["psutil", "click"]
# ///
"""Kill processes by port, name, or PID."""
import subprocess
import sys

import click
import psutil


def get_pid_on_port(port: int) -> int | None:
    for conn in psutil.net_connections(kind="inet"):
        if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
            return conn.pid
    return None


def find_pid(name: str) -> int | None:
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if name.lower() in proc.info["name"].lower():
                return proc.info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def kill(pid: int, name: str | None = None) -> bool:
    label = f"{name} ({pid})" if name else str(pid)
    click.echo(f"Sending SIGTERM to {label}...")

    try:
        proc = psutil.Process(pid)
        proc.terminate()
    except psutil.NoSuchProcess:
        click.secho(f"✓ {label} already gone", fg="green")
        return True
    except psutil.Error as e:
        click.secho(f"Failed to terminate: {e}", fg="red", err=True)
        return False

    # Wait up to 5 seconds
    try:
        proc.wait(timeout=5)
        click.secho(f"✓ {label} killed gracefully", fg="green")
        return True
    except psutil.TimeoutExpired:
        pass

    # Force kill
    click.echo(f"Force killing {label} with SIGKILL...")
    try:
        proc.kill()
        proc.wait(timeout=2)
        click.secho(f"✓ {label} killed with SIGKILL", fg="green")
        return True
    except psutil.Error as e:
        click.secho(f"✗ Failed to kill {label}: {e}", fg="red", err=True)
        return False


@click.group()
def cli():
    """Kill processes by port, name, or PID."""
    pass


@cli.command()
@click.argument("port", type=int)
def port(port: int) -> None:
    """Kill process on a given port."""
    pid = get_pid_on_port(port)
    if pid is None:
        click.secho(f"No process on port {port}", fg="red", err=True)
        raise sys.exit(1)
    click.echo(f"Found PID {pid} on port {port}")
    sys.exit(0 if kill(pid, f"port {port}") else 1)


@cli.command()
@click.argument("name")
@click.option("-r", "--restart", is_flag=True, help="restart after killing")
def name(name: str, restart: bool) -> None:
    """Kill process by name."""
    pid = find_pid(name)
    if pid is None:
        click.secho(f"No process named '{name}'", fg="red", err=True)
        raise sys.exit(1)
    success = kill(pid, name)
    if restart and success:
        click.echo(f"Restarting {name}...")
        subprocess.Popen(name, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sys.exit(0 if success else 1)


@cli.command()
@click.argument("pid", type=int)
def pid(pid: int) -> None:
    """Kill process by PID."""
    sys.exit(0 if kill(pid) else 1)


if __name__ == "__main__":
    cli()
