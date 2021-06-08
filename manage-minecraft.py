#!/usr/bin/env python
import subprocess
from pathlib import Path
import pprint
import inquirer
from jproperties import Properties

# Configuration variables
service_name = "minecraft.service"
properties_path = "./server.properties"
worlds_path = "./saves"
mc_rcon_path = "./mcrcon/mcrcon"
rcon_port = "25575"
rcon_password = "thisIsMyRconPassword"


def server_is_running():
    return subprocess.run(
        ["systemctl", "--quiet", "is-active", service_name]
    ).returncode == 0


# Base function for subprocesses that require Ctrl+C (SIGINT) to close
def handle_sigint(*args):
    try:
        subprocess.run(list(args))
    except KeyboardInterrupt:
        pass
    print()


def rcon_terminal():
    handle_sigint(mc_rcon_path, "-H", "127.0.0.1", "-P", rcon_port,
                  "-p", rcon_password, "-t")


def view_logs():
    subprocess.run(["journalctl", "-b", "-u", service_name])


def follow_logs():
    handle_sigint("journalctl", "-f", "-b", "-u", service_name)


# Base function for sudo systemctl commands
def sudo_systemctl_command(cmd, cmd_ing, follow):
    result = subprocess.run(
        ["sudo", "systemctl", cmd, service_name]
    ).returncode
    print(f"Server {cmd_ing + '...' if result == 0 else cmd + ' failed!'}")
    if follow:
        follow_logs()


def start_server(follow=True):
    sudo_systemctl_command("start", "\033[92mstarting\033[0m", follow)


def stop_server(follow=True):
    sudo_systemctl_command("stop", "\033[91mstopping\033[0m", follow)


# Intentionally not using systemctl restart to allow graceful stopping
def restart_server():
    stop_server(follow=False)
    print("Close the logs with \033[93mCtrl+C\033[0m when the server has",
          "finished saving chunks.")
    follow_logs()
    print()
    start_server()


def load_world_and_config():
    # Get current properties
    props = Properties()
    with open(properties_path, "rb") as f:
        props.load(f, "utf-8")

    # Select world
    world_list = [x.name for x in Path(worlds_path).iterdir() if x.is_dir()]
    level_name = inquirer.prompt([
        inquirer.List(
            "level-name",
            message="Select a world",
            choices=world_list,
            default=props["level-name"].data
        ),
    ])["level-name"]

    # Load world's configuration
    world_props_path = Path(worlds_path, level_name + ".properties")
    world_props = Properties()
    if world_props_path.is_file():
        with open(world_props_path, "rb") as f:
            world_props.load(f, "utf-8")
    else:
        print("No configuration found for this world\n")
    world_props["level-name"] = level_name
    props.update(world_props)

    print("Writing following config to server.properties:")
    pprint.pprint(world_props.properties)
    print()
    with open(properties_path, "wb") as f:
        props.store(f, encoding="utf-8")

    # Prompt for restart/start
    action = inquirer.prompt([
        inquirer.Confirm(
            "action",
            message=f"{'Restart' if server_is_running() else 'Start'} server?",
            default=True
        ),
    ])["action"]
    if action:
        restart_server() if server_is_running() else start_server()


if __name__ == "__main__":
    running = server_is_running()
    menu_options = [
        ("Load world and config", load_world_and_config),
        ("Connect to server terminal", rcon_terminal),
        ("View server logs", view_logs),
    ]
    if running:
        menu_options.extend([
            ("Follow server logs", follow_logs),
            ("Restart server", restart_server),
            ("Stop server", stop_server)
        ])
    else:
        menu_options.append(("Start server", start_server))

    print(
        "Server is",
        "\033[92mrunning\033[0m!" if running else "\033[91mstopped\033[0m!"
    )

    answer = inquirer.prompt([
        inquirer.List(
            "menu_choice",
            message="Select an action",
            choices=menu_options,
        ),
    ])
    if answer is not None:
        answer["menu_choice"]()
