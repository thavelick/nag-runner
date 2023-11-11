#!/usr/bin/python3
import argparse
import json
import os
from datetime import datetime, timedelta
from subprocess import call


class InvalidConfigException(Exception):
    "Raised when the config is invalid."


class MissingConfigException(Exception):
    "Raised when the config is missing."


def print_menu():
    "print the help menu"

    print(
        """
    Possible responses are:
    y: Run the command
    n: Do not run the command, but still nag me next time
    d: don't run the command this time and reset the interval. This is useful if
         you've  run the command outside of nag_runner recently
    ?: Show this help message
    """
    )


class NagRunner:
    def __init__(self, config_path, last_run_path=None):
        self.config = self.load_config(config_path)
        self.last_run_path = last_run_path or self.get_default_last_run_path()

    def load_config(self, config_file=None):
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

    def get_default_last_run_path(self):
        "Returns the default path to the last run file."
        return os.path.join(
            os.path.expanduser("~"), ".cache", "nag_runner", "last_run.json"
        )

    def get_last_run(self, name):
        "Returns the last run time for a command."
        if not os.path.exists(self.last_run_path):
            return None

        with open(self.last_run_path, "r", encoding="utf-8") as file:
            last_run = json.load(file)

        if name not in last_run:
            return None

        return datetime.strptime(last_run[name], "%Y-%m-%dT%H:%M:%S.%f")

    def set_last_run(self, name):
        "Sets the last run time for a command."
        last_run = {}
        if os.path.exists(self.last_run_path):
            with open(self.last_run_path, "r", encoding="utf-8") as file:
                last_run = json.load(file)
        else:
            os.makedirs(os.path.dirname(self.last_run_path), exist_ok=True)
        last_run[name] = datetime.now().isoformat()
        with open(self.last_run_path, "w", encoding="utf-8") as file:
            json.dump(last_run, file)

    def get_entry_by_name(self, name):
        "Returns the entry with the given name."
        for entry in self.config:
            if entry["name"] == name:
                return entry

        return None


def main():
    """
    Main function.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-path", "-c", help="Path to the config file")
    parser.add_argument("--last-run-path", "-l", help="Path to the last run file")
    parser.add_argument("--name", "-n", help="Name of a single entry to run")
    args = parser.parse_args()
    entry_name_to_run = args.name
    config_path = args.config_path
    last_run_path = args.last_run_path

    nag_runner = NagRunner(config_path, last_run_path)

    if entry_name_to_run:
        entry = nag_runner.get_entry_by_name(entry_name_to_run)
        if entry is None:
            print(f"Could not find entry with name {entry_name_to_run}")
            exit(1)

        command = entry["command"]
        call(command, shell=True)
        nag_runner.set_last_run(entry_name_to_run)
        exit(0)

    prompt_options = "Y/n/d/?"
    for entry in nag_runner.config:
        for key in ["interval", "command", "name"]:
            if key not in entry:
                raise InvalidConfigException(f"No {key} specified")

        interval = entry["interval"]
        command = entry["command"]
        name = entry["name"]

        last_run = nag_runner.get_last_run(name)
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
            nag_runner.set_last_run(name)
        elif response == "d":
            nag_runner.set_last_run(name)
        else:
            print("Ok, I'll nag you next time")


if __name__ == "__main__":
    try:
        main()
    except (InvalidConfigException, MissingConfigException) as e:
        print(e)
        exit(1)
