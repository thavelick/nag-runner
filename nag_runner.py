#!/usr/bin/python3
"""
Reminds you to run important commands on a regular basis.

Usage: nag_runner.py [CONFIG_JSON] [LAST_RUN_JSON]


    CONFIG_JSON:
        A JSON file containing the configuration. If not provided it will be
        loaded from $HOME/.nag_runner.json or $HOME/.config/nag_runner.json.


        Example config:
        [
            {
                "name": "archlinux updates",
                "command": "sudo pacman -Syu",
                "interval": "1"
            }
        ]

    LAST_RUN_JSON:
        A JSON file containing the last run time for each command. If not provided
        it will be loaded from .$HOME/.cache/nag_runner/last_run.json) or
        created there.

When run, if the command has not been run in the last interval, nag_runner will
ask you to run the command:

    $ nag_runner.py
    It was been 7 days since you've run "archlinux updates". Run now? [Y/n/d/?]?

Possible responses are:
    y: Run the command
    n: Do not run the command, but still nag me next time
    d: don't run the command this time and reset the interval. This is useful if
         you've  run the command outside of nag_runner recently
    ?: Show a help message with possible responses
"""
import json
import os
import sys
from datetime import datetime, timedelta
from subprocess import call

class InvalidConfigException(Exception):
    "Raised when the config is invalid."


class MissingConfigException(Exception):
    "Raised when the config is missing."


def load_config(config_file=None):
    """
    Loads the config file.
    """
    if config_file is None:
        possible_config_files = [
            os.path.join(os.path.expanduser("~"), ".config", "nag_runner.json"),
            os.path.join(os.path.expanduser("~"), ".nag_runner.json"),
        ]

        for config_file in possible_config_files:
            if os.path.exists(config_file):
                break
        else:
            possible_config_files_string = ", ".join(possible_config_files)
            raise MissingConfigException(
                f"No config file found in {possible_config_files_string}"
            )

    with open(config_file, "r", encoding="utf-8") as file:
        return json.load(file)

def print_menu():
    "print the help menu"

    print("""
    Possible responses are:
    y: Run the command
    n: Do not run the command, but still nag me next time
    d: don't run the command this time and reset the interval. This is useful if
         you've  run the command outside of nag_runner recently
    ?: Show this help message
    """)

def get_last_run_path():
    """
    Returns the path to the last run file.
    """
    return os.path.join(
        os.path.expanduser("~"), ".cache", "nag_runner", "last_run.json"
    )

def set_last_run(name, last_run_file=None):
    """
    Sets the last run time for a command.
    """
    last_run = {}

    if last_run_file is None:
        last_run_file = get_last_run_path()

    if os.path.exists(last_run_file):
        with open(last_run_file, "r", encoding='utf-8') as file:
            last_run = json.load(file)
    else:
        os.makedirs(os.path.dirname(last_run_file), exist_ok=True)

    last_run[name] = datetime.now().isoformat()
    with open(last_run_file, "w", encoding='utf-8') as file:
        json.dump(last_run, file)

def get_last_run(name, last_run_file=None):
    """
    Returns the last run time for a command.
    """
    if last_run_file is None:
        last_run_file = get_last_run_path()

    if not os.path.exists(last_run_file):
        return None

    with open(last_run_file, "r", encoding='utf-8') as file:
        last_run = json.load(file)

    if name not in last_run:
        return None

    return datetime.strptime(last_run[name], "%Y-%m-%dT%H:%M:%S.%f")

def main():
    """
    Main function.
    """

    first_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if first_arg == "--help" or first_arg == "-h":
        print(__doc__)
        exit(0)

    prompt_options = "Y/n/d/?"
    config_path = first_arg
    last_run_path = sys.argv[2] if len(sys.argv) > 2 else None
    config = load_config(config_path)
    for entry in config:

        for key in ["interval", "command", "name"]:
            if key not in entry:
                raise InvalidConfigException(f"No {key} specified")

        interval = entry["interval"]
        command = entry["command"]
        name = entry["name"]

        last_run = get_last_run(name, last_run_path)
        if last_run:
            delta = datetime.now() - last_run
            if delta < timedelta(days=int(interval)):
                continue

            prompt = (
                f"It was been {delta.days} days since you've run {name}. "
                f"Run now? [{prompt_options}]? "
            )
        else:
            prompt = f"You've never run {name}. Run now? [{prompt_options}]? "

        response = None
        while response is None:
            print(prompt, end="")
            response = input()
            if response == "?":
                print_menu()
                response = None

        if response in ["y", "Y", ""]:
            call(command, shell=True)
            set_last_run(name, last_run_path)
        elif response == "d":
            # the user already ran the command manually so just set the last run
            # time to now
            set_last_run(name, last_run_path)
        else:
            print("Ok, I'll nag you next time")

if __name__ == "__main__":
    try:
        main()
    except (InvalidConfigException, MissingConfigException) as e:
        print(e)
        exit(1)
